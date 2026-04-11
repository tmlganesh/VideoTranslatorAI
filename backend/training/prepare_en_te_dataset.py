"""
Offline data pipeline for English↔Telugu translation fine-tuning.

Pipeline goals:
- Primary source (70%): ai4bharat/samanantar (te)
- Secondary source (30%): OpenSubtitles from OPUS
- Clean, filter, and normalize for spoken/conversational translation
- Export unified records and mT5-ready prompt format

Usage:
    python backend/training/prepare_en_te_dataset.py --output-dir ./Datasets/en_te --target-pairs 200000
"""

from __future__ import annotations

import argparse
import json
import random
import re
import zipfile
import unicodedata
from dataclasses import dataclass
from io import TextIOWrapper
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import requests
from datasets import Dataset, load_dataset
from transformers import AutoTokenizer


TELUGU_PATTERN = re.compile(r"[\u0C00-\u0C7F]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")
WHITESPACE_PATTERN = re.compile(r"\s+")

# Basic domain filters to avoid formal/legal/news-heavy content.
FORMAL_BLOCKLIST = {
    "whereas",
    "hereby",
    "plaintiff",
    "defendant",
    "notwithstanding",
    "section",
    "act,",
    "gazette",
    "parliament",
    "stock market",
    "breaking news",
    "editorial",
    "press release",
}


@dataclass
class DatasetStats:
    name: str
    scanned_rows: int = 0
    accepted_rows: int = 0
    skipped_empty: int = 0
    skipped_script: int = 0
    skipped_mismatch: int = 0
    skipped_duplicate: int = 0
    skipped_length: int = 0
    skipped_formal: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare EN↔TE fine-tuning dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for processed datasets (default: <repo>/Datasets/en_te)",
    )
    parser.add_argument("--target-pairs", type=int, default=200_000)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--samanantar-ratio", type=float, default=0.70)
    parser.add_argument("--opensubs-ratio", type=float, default=0.30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lowercase", action="store_true")
    parser.add_argument("--tokenizer", type=str, default="google/mt5-small")
    return parser.parse_args()


def default_output_dir() -> Path:
    # Script path: <repo>/backend/training/prepare_en_te_dataset.py
    # Repo root is parents[2].
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Datasets" / "en_te"


def normalize_text(text: Optional[str], lowercase: bool = False) -> str:
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()
    if lowercase:
        normalized = normalized.lower()
    return normalized


def looks_formal_or_news_like(source_text: str, target_text: str) -> bool:
    merged = f"{source_text} {target_text}".lower()
    if any(term in merged for term in FORMAL_BLOCKLIST):
        return True

    # Keep subtitle-like / spoken style by limiting overly long paragraphs.
    if len(source_text) > 280 or len(target_text) > 280:
        return True
    if source_text.count(".") > 3 or target_text.count(".") > 3:
        return True
    if len(source_text.split()) > 40 or len(target_text.split()) > 40:
        return True

    return False


def looks_misaligned(source_text: str, target_text: str) -> bool:
    source_words = max(1, len(source_text.split()))
    target_words = max(1, len(target_text.split()))
    ratio = max(source_words, target_words) / min(source_words, target_words)

    if ratio > 3.2:
        return True
    if source_text.casefold() == target_text.casefold() and source_words > 2:
        return True
    return False


def has_expected_scripts(source_text: str, target_text: str) -> bool:
    # We expect EN source and TE target in canonical training set.
    return bool(LATIN_PATTERN.search(source_text)) and bool(TELUGU_PATTERN.search(target_text))


def token_length_ok(tokenizer, source_text: str, target_text: str, max_tokens: int) -> bool:
    source_len = len(tokenizer.encode(source_text, add_special_tokens=False))
    target_len = len(tokenizer.encode(target_text, add_special_tokens=False))
    return source_len <= max_tokens and target_len <= max_tokens


def resolve_parallel_extractor(sample: Dict) -> Callable[[Dict], Tuple[Optional[str], Optional[str]]]:
    # Common huggingface translation field.
    translation_obj = sample.get("translation")
    if isinstance(translation_obj, dict):
        if "en" in translation_obj and "te" in translation_obj:
            return lambda row: (row["translation"].get("en"), row["translation"].get("te"))

    candidate_pairs = [
        ("en", "te"),
        ("english", "telugu"),
        ("source", "target"),
        ("src", "tgt"),
        ("src_sentence", "tgt_sentence"),
        ("sentence1", "sentence2"),
    ]
    for source_key, target_key in candidate_pairs:
        if source_key in sample and target_key in sample:
            return lambda row, sk=source_key, tk=target_key: (row.get(sk), row.get(tk))

    raise ValueError(
        "Could not infer EN/TE columns. Expected translation dict or known key pair."
    )


def load_samanantar_dataset():
    print("Loading primary dataset: ai4bharat/samanantar (te)...")
    ds = load_dataset("ai4bharat/samanantar", "te", split="train")
    return ds, "ai4bharat/samanantar:te"


def load_opensubtitles_dataset():
    print("Loading secondary dataset: OpenSubtitles from OPUS...")
    attempts = [
        ("open_subtitles", None, {"lang1": "en", "lang2": "te"}),
        ("open_subtitles", "en-te", {}),
        ("OpenSubtitles/open_subtitles", "en-te", {}),
        ("opus_open_subtitles", "en-te", {}),
    ]

    errors: List[str] = []
    for path, config_name, config_kwargs in attempts:
        try:
            ds = load_dataset(
                path,
                name=config_name,
                split="train",
                **config_kwargs,
            )
            return ds, f"{path}:{config_name or 'default'}"
        except Exception as exc:
            errors.append(f"{path}:{config_name or 'default'} -> {exc}")

    error_lines = "\n".join(errors)

    print("HuggingFace OpenSubtitles loaders failed. Falling back to direct OPUS download...")
    print(f"HF attempt errors:\n{error_lines}")

    opus_url_candidates = [
        "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/moses/en-te.txt.zip",
        "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2016/moses/en-te.txt.zip",
    ]

    repo_root = Path(__file__).resolve().parents[2]
    downloads_dir = repo_root / "Datasets" / "_downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    last_error = None
    combined_rows: List[Dict] = []
    seen_pairs = set()
    for url in opus_url_candidates:
        zip_name = url.split("/")[-1]
        zip_path = downloads_dir / zip_name
        try:
            if not zip_path.exists():
                print(f"Downloading OpenSubtitles from OPUS: {url}")
                with requests.get(url, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with zip_path.open("wb") as out:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                out.write(chunk)
            else:
                print(f"Using cached OPUS archive: {zip_path}")

            with zipfile.ZipFile(zip_path, "r") as archive:
                file_names = archive.namelist()
                en_file = next((name for name in file_names if name.endswith(".en")), None)
                te_file = next((name for name in file_names if name.endswith(".te")), None)

                if not en_file or not te_file:
                    raise RuntimeError("Could not find .en/.te files in OPUS archive")

                rows = []
                max_rows = 600_000
                with archive.open(en_file) as en_handle, archive.open(te_file) as te_handle:
                    en_stream = TextIOWrapper(en_handle, encoding="utf-8", errors="ignore")
                    te_stream = TextIOWrapper(te_handle, encoding="utf-8", errors="ignore")

                    for en_line, te_line in zip(en_stream, te_stream):
                        en_text = en_line.strip()
                        te_text = te_line.strip()
                        if en_text and te_text:
                            rows.append({"en": en_text, "te": te_text})
                        if len(rows) >= max_rows:
                            break

                if not rows:
                    raise RuntimeError("OPUS OpenSubtitles archive produced zero rows")

                added = 0
                for row in rows:
                    key = (row["en"], row["te"])
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    combined_rows.append(row)
                    added += 1

                print(
                    f"Loaded {len(rows)} rows from {zip_name}; "
                    f"added {added} unique rows (total unique: {len(combined_rows)})"
                )
        except Exception as exc:
            last_error = exc
            print(f"Failed OPUS URL {url}: {exc}")

    if combined_rows:
        return Dataset.from_list(combined_rows), "OPUS-OpenSubtitles-direct:multi-archive"

    raise RuntimeError(
        "Failed to load OpenSubtitles data from both HuggingFace and direct OPUS fallback. "
        f"Last fallback error: {last_error}"
    )


def collect_clean_rows(
    dataset,
    extractor: Callable[[Dict], Tuple[Optional[str], Optional[str]]],
    tokenizer,
    quota: int,
    max_tokens: int,
    lowercase: bool,
    stats: DatasetStats,
    global_dedupe: set,
) -> List[Dict]:
    collected: List[Dict] = []

    for row in dataset:
        stats.scanned_rows += 1
        source_raw, target_raw = extractor(row)

        source_text = normalize_text(source_raw, lowercase=lowercase)
        target_text = normalize_text(target_raw, lowercase=lowercase)

        if not source_text or not target_text:
            stats.skipped_empty += 1
            continue
        if not has_expected_scripts(source_text, target_text):
            stats.skipped_script += 1
            continue
        if looks_misaligned(source_text, target_text):
            stats.skipped_mismatch += 1
            continue
        if looks_formal_or_news_like(source_text, target_text):
            stats.skipped_formal += 1
            continue
        if not token_length_ok(tokenizer, source_text, target_text, max_tokens=max_tokens):
            stats.skipped_length += 1
            continue

        dedupe_key = (source_text, target_text)
        if dedupe_key in global_dedupe:
            stats.skipped_duplicate += 1
            continue

        global_dedupe.add(dedupe_key)
        collected.append(
            {
                "source_text": source_text,
                "target_text": target_text,
                "source_lang": "en",
                "target_lang": "te",
            }
        )
        stats.accepted_rows += 1

        if len(collected) >= quota:
            break

    return collected


def to_mt5_record(row: Dict) -> Dict:
    return {
        **row,
        "input_text": f"translate en to te: {row['source_text']}",
        "target_text_mt5": row["target_text"],
    }


def save_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_rows(rows: List[Dict], seed: int) -> Dict[str, List[Dict]]:
    random.Random(seed).shuffle(rows)
    n_total = len(rows)
    train_end = int(n_total * 0.98)
    val_end = int(n_total * 0.99)
    return {
        "train": rows[:train_end],
        "validation": rows[train_end:val_end],
        "test": rows[val_end:],
    }


def print_stats(stats: DatasetStats) -> None:
    print(f"\n=== {stats.name} STATS ===")
    print(f"Scanned      : {stats.scanned_rows}")
    print(f"Accepted     : {stats.accepted_rows}")
    print(f"Skipped empty: {stats.skipped_empty}")
    print(f"Skipped script mismatch: {stats.skipped_script}")
    print(f"Skipped misaligned: {stats.skipped_mismatch}")
    print(f"Skipped duplicates: {stats.skipped_duplicate}")
    print(f"Skipped long tokens: {stats.skipped_length}")
    print(f"Skipped formal/news: {stats.skipped_formal}")


def main() -> None:
    args = parse_args()

    if abs((args.samanantar_ratio + args.opensubs_ratio) - 1.0) > 1e-6:
        raise ValueError("samanantar-ratio + opensubs-ratio must equal 1.0")

    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir()
    split_dir = output_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    samanantar_quota = int(args.target_pairs * args.samanantar_ratio)
    opensubs_quota = args.target_pairs - samanantar_quota

    dedupe_store = set()

    samanantar_ds, samanantar_name = load_samanantar_dataset()
    samanantar_extractor = resolve_parallel_extractor(samanantar_ds[0])
    samanantar_stats = DatasetStats(name=samanantar_name)
    samanantar_rows = collect_clean_rows(
        dataset=samanantar_ds,
        extractor=samanantar_extractor,
        tokenizer=tokenizer,
        quota=samanantar_quota,
        max_tokens=args.max_tokens,
        lowercase=args.lowercase,
        stats=samanantar_stats,
        global_dedupe=dedupe_store,
    )

    opensubs_ds, opensubs_name = load_opensubtitles_dataset()
    opensubs_extractor = resolve_parallel_extractor(opensubs_ds[0])
    opensubs_stats = DatasetStats(name=opensubs_name)
    opensubs_rows = collect_clean_rows(
        dataset=opensubs_ds,
        extractor=opensubs_extractor,
        tokenizer=tokenizer,
        quota=opensubs_quota,
        max_tokens=args.max_tokens,
        lowercase=args.lowercase,
        stats=opensubs_stats,
        global_dedupe=dedupe_store,
    )

    if len(samanantar_rows) == 0 or len(opensubs_rows) == 0:
        raise RuntimeError(
            "Insufficient cleaned rows: one or both datasets produced zero usable pairs."
        )

    # If one dataset is smaller than requested quota, auto-scale final size while
    # preserving the configured mix ratio as closely as possible.
    max_pairs_from_samanantar = int(len(samanantar_rows) / args.samanantar_ratio)
    max_pairs_from_opensubs = int(len(opensubs_rows) / args.opensubs_ratio)
    effective_target_pairs = min(args.target_pairs, max_pairs_from_samanantar, max_pairs_from_opensubs)

    if effective_target_pairs <= 0:
        raise RuntimeError("Unable to compute a positive effective target pair count.")

    effective_samanantar_quota = int(effective_target_pairs * args.samanantar_ratio)
    effective_opensubs_quota = effective_target_pairs - effective_samanantar_quota

    if effective_samanantar_quota <= 0 or effective_opensubs_quota <= 0:
        raise RuntimeError("Effective quotas are invalid after scaling.")

    if effective_target_pairs < args.target_pairs:
        print(
            "WARNING: Requested target pairs could not be met with available cleaned data. "
            f"Requested={args.target_pairs}, Effective={effective_target_pairs}."
        )

    samanantar_rows = samanantar_rows[:effective_samanantar_quota]
    opensubs_rows = opensubs_rows[:effective_opensubs_quota]

    combined_rows = samanantar_rows + opensubs_rows
    random.Random(args.seed).shuffle(combined_rows)

    splits = split_rows(combined_rows, seed=args.seed)

    # Unified dataset output requested by system design.
    save_jsonl(output_dir / "en_te_unified.jsonl", combined_rows)
    save_jsonl(split_dir / "train.jsonl", splits["train"])
    save_jsonl(split_dir / "validation.jsonl", splits["validation"])
    save_jsonl(split_dir / "test.jsonl", splits["test"])

    # mT5 prompt-formatted outputs.
    train_mt5 = [to_mt5_record(row) for row in splits["train"]]
    val_mt5 = [to_mt5_record(row) for row in splits["validation"]]
    test_mt5 = [to_mt5_record(row) for row in splits["test"]]

    save_jsonl(split_dir / "train_mt5.jsonl", train_mt5)
    save_jsonl(split_dir / "validation_mt5.jsonl", val_mt5)
    save_jsonl(split_dir / "test_mt5.jsonl", test_mt5)

    # Convenience export similar to the user-provided snippet.
    Dataset.from_list(combined_rows).to_json(str(output_dir / "en_te_dataset.json"))

    metadata = {
        "requested_target_pairs": args.target_pairs,
        "effective_target_pairs": effective_target_pairs,
        "final_pairs": len(combined_rows),
        "composition": {
            "samanantar_ratio": args.samanantar_ratio,
            "opensubs_ratio": args.opensubs_ratio,
            "samanantar_rows": len(samanantar_rows),
            "opensubs_rows": len(opensubs_rows),
        },
        "filters": {
            "max_tokens": args.max_tokens,
            "lowercase": args.lowercase,
            "spoken_priority": True,
        },
        "splits": {k: len(v) for k, v in splits.items()},
        "datasets": {
            "primary": samanantar_name,
            "secondary": opensubs_name,
        },
    }

    with (output_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)

    print_stats(samanantar_stats)
    print_stats(opensubs_stats)
    print("\nSaved dataset artifacts to:", output_dir)
    print("Metadata:")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
