"""
Evaluate a trained mT5 checkpoint for EN↔TE translation with BLEU + chrF.

Usage:
    python backend/training/evaluate_mt5_en_te.py --model-dir ./backend/training/models/mt5-en-te --dataset-dir ./Datasets/en_te --direction en-te
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import evaluate
import torch
from datasets import load_dataset
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate mT5 EN↔TE model")
    parser.add_argument("--model-dir", required=True, type=str)
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Prepared dataset directory (default: <repo>/Datasets/en_te)",
    )
    parser.add_argument("--direction", choices=["en-te", "te-en"], default="en-te")
    parser.add_argument("--max-source-length", type=int, default=128)
    parser.add_argument("--max-target-length", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--sample-count", type=int, default=5000)
    parser.add_argument("--output-file", type=str, default="evaluation_results.json")
    return parser.parse_args()


def default_dataset_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Datasets" / "en_te"


def make_prompt_and_target(row: Dict, direction: str):
    if direction == "en-te":
        prompt = f"translate en to te: {row['source_text']}"
        target = row["target_text"]
    else:
        prompt = f"translate te to en: {row['target_text']}"
        target = row["source_text"]
    return prompt, target


def batched(items: List[Dict], batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def main() -> None:
    args = parse_args()

    dataset_dir = Path(args.dataset_dir).resolve() if args.dataset_dir else default_dataset_dir()
    model_dir = Path(args.model_dir).resolve()

    test_data = load_dataset(
        "json",
        data_files={"test": str(dataset_dir / "splits" / "test.jsonl")},
    )["test"]

    if args.sample_count > 0 and len(test_data) > args.sample_count:
        test_data = test_data.select(range(args.sample_count))

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(model_dir))
    model.eval()

    predictions: List[str] = []
    references: List[str] = []

    rows = [test_data[i] for i in range(len(test_data))]

    for batch_rows in batched(rows, args.batch_size):
        prompts = []
        batch_targets = []
        for row in batch_rows:
            prompt, target = make_prompt_and_target(row, args.direction)
            prompts.append(prompt)
            batch_targets.append(target)

        encoded = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=args.max_source_length,
        )

        with torch.no_grad():
            outputs = model.generate(
                **encoded,
                max_length=args.max_target_length,
                num_beams=5,
                no_repeat_ngram_size=2,
                early_stopping=True,
            )

        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend([text.strip() for text in decoded])
        references.extend([text.strip() for text in batch_targets])

    bleu = evaluate.load("sacrebleu")
    chrf = evaluate.load("chrf")

    bleu_score = bleu.compute(predictions=predictions, references=[[r] for r in references])["score"]
    chrf_score = chrf.compute(predictions=predictions, references=references)["score"]

    results = {
        "model_dir": str(model_dir),
        "direction": args.direction,
        "samples": len(predictions),
        "bleu": round(float(bleu_score), 4),
        "chrf": round(float(chrf_score), 4),
        "examples": [
            {
                "prediction": predictions[i],
                "reference": references[i],
            }
            for i in range(min(10, len(predictions)))
        ],
    }

    output_path = model_dir / args.output_file
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
