"""
Train mT5 for EN↔TE translation using prepared offline dataset artifacts.

Usage (Phase 1 baseline EN->TE):
    python backend/training/train_mt5_en_te.py --dataset-dir ./Datasets/en_te --output-dir ./backend/training/models/mt5-en-te --direction en-te

Usage (Phase 2 optional bilingual):
    python backend/training/train_mt5_en_te.py --dataset-dir ./Datasets/en_te --output-dir ./backend/training/models/mt5-en-te-bilingual --direction both
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import evaluate
import numpy as np
import torch
from datasets import concatenate_datasets, load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune mT5 for EN↔TE translation")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Prepared dataset directory (default: <repo>/Datasets/en_te)",
    )
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--base-model", type=str, default="google/mt5-small")
    parser.add_argument("--direction", choices=["en-te", "te-en", "both"], default="en-te")
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--max-source-length", type=int, default=128)
    parser.add_argument("--max-target-length", type=int, default=128)
    parser.add_argument("--eval-steps", type=int, default=1000)
    parser.add_argument("--save-steps", type=int, default=1000)
    parser.add_argument("--logging-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--low-memory-mode",
        action="store_true",
        help="Freeze most model weights and train only layer-norm parameters to reduce RAM usage",
    )
    return parser.parse_args()


def default_dataset_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "Datasets" / "en_te"


def _format_translation_pair(example: Dict, direction: str) -> Dict:
    if direction == "en-te":
        source_text = example["source_text"]
        target_text = example["target_text"]
        prompt = f"translate en to te: {source_text}"
    elif direction == "te-en":
        source_text = example["target_text"]
        target_text = example["source_text"]
        prompt = f"translate te to en: {source_text}"
    else:
        raise ValueError(f"Unsupported direction: {direction}")

    return {"input_text": prompt, "target_text": target_text}


def build_directional_dataset(raw_dataset, direction: str):
    if direction in {"en-te", "te-en"}:
        return raw_dataset.map(lambda ex: _format_translation_pair(ex, direction))

    if direction == "both":
        en_te = raw_dataset.map(lambda ex: _format_translation_pair(ex, "en-te"))
        te_en = raw_dataset.map(lambda ex: _format_translation_pair(ex, "te-en"))
        combined = {
            split: concatenate_datasets([en_te[split], te_en[split]])
            for split in en_te.keys()
        }
        for split in combined:
            combined[split] = combined[split].shuffle(seed=42)
        return combined

    raise ValueError(f"Unsupported direction mode: {direction}")


def enable_low_memory_mode(model) -> int:
    """Freeze most parameters and keep only layer norm params trainable."""
    for param in model.parameters():
        param.requires_grad = False

    trainable_count = 0
    for name, param in model.named_parameters():
        lname = name.lower()
        if "layer_norm" in lname:
            param.requires_grad = True
            trainable_count += param.numel()

    if trainable_count == 0:
        raise RuntimeError("Low-memory mode found no trainable layer-norm parameters.")

    return trainable_count


def main() -> None:
    args = parse_args()

    dataset_dir = Path(args.dataset_dir).resolve() if args.dataset_dir else default_dataset_dir()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data_files = {
        "train": str(dataset_dir / "splits" / "train.jsonl"),
        "validation": str(dataset_dir / "splits" / "validation.jsonl"),
        "test": str(dataset_dir / "splits" / "test.jsonl"),
    }

    raw_dataset = load_dataset("json", data_files=data_files)
    directional_dataset = build_directional_dataset(raw_dataset, args.direction)

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.base_model)

    trainable_params = None
    if args.low_memory_mode:
        trainable_params = enable_low_memory_mode(model)
        print(f"Low-memory mode enabled. Trainable params: {trainable_params}")

    def tokenize_batch(batch):
        model_inputs = tokenizer(
            batch["input_text"],
            max_length=args.max_source_length,
            truncation=True,
        )
        labels = tokenizer(
            text_target=batch["target_text"],
            max_length=args.max_target_length,
            truncation=True,
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = directional_dataset.map(
        tokenize_batch,
        batched=True,
        remove_columns=directional_dataset["train"].column_names,
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    bleu = evaluate.load("sacrebleu")
    chrf = evaluate.load("chrf")

    def compute_metrics(eval_preds):
        predictions, labels = eval_preds
        if isinstance(predictions, tuple):
            predictions = predictions[0]

        decoded_predictions = tokenizer.batch_decode(predictions, skip_special_tokens=True)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

        decoded_predictions = [text.strip() for text in decoded_predictions]
        decoded_labels = [text.strip() for text in decoded_labels]

        bleu_score = bleu.compute(
            predictions=decoded_predictions,
            references=[[label] for label in decoded_labels],
        )["score"]
        chrf_score = chrf.compute(
            predictions=decoded_predictions,
            references=decoded_labels,
        )["score"]

        return {
            "bleu": round(float(bleu_score), 4),
            "chrf": round(float(chrf_score), 4),
        }

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        save_total_limit=3,
        predict_with_generate=True,
        generation_max_length=args.max_target_length,
        load_best_model_at_end=True,
        metric_for_best_model="chrf",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),
        report_to="none",
        seed=args.seed,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    metrics = trainer.evaluate(tokenized_dataset["test"])

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    run_config = {
        "base_model": args.base_model,
        "direction": args.direction,
        "epochs": args.epochs,
        "max_steps": args.max_steps,
        "low_memory_mode": args.low_memory_mode,
        "trainable_params": trainable_params,
        "learning_rate": args.learning_rate,
        "max_source_length": args.max_source_length,
        "max_target_length": args.max_target_length,
        "metrics": metrics,
    }

    with (output_dir / "training_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(run_config, handle, indent=2, ensure_ascii=False)

    print("Training complete.")
    print(json.dumps(run_config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
