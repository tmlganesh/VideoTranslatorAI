# EN<->TE mT5 Training Pipeline (Offline)

This folder contains the offline training pipeline. Backend inference must remain separate.

No virtual environment is required for this workflow. Install dependencies directly in your current Python environment.

## 1) Install Training Dependencies

From repository root:

python -m pip install -r backend/training/requirements.txt

## 2) Prepare Dataset (Mandatory)

Build the 70/30 blended dataset:
- 70% Samanantar (ai4bharat/samanantar, te split)
- 30% OpenSubtitles (OPUS)

Command:

python backend/training/prepare_en_te_dataset.py --output-dir ./Datasets/en_te --target-pairs 200000 --max-tokens 128

Outputs include:
- en_te_unified.jsonl
- splits/train.jsonl
- splits/validation.jsonl
- splits/test.jsonl
- splits/train_mt5.jsonl (prompt formatted)
- metadata.json

Unified row format:
{
  "source_text": "...",
  "target_text": "...",
  "source_lang": "en",
  "target_lang": "te"
}

mT5 prompt format:
- Input:  translate en to te: <source_text>
- Target: <target_text>

## 3) Train mT5

Phase 1 baseline (EN->TE):

python backend/training/train.py --dataset-dir ./Datasets/en_te --output-dir ./backend/training/models/mt5-en-te --direction en-te

Phase 2 optional bilingual (EN<->TE):

python backend/training/train.py --dataset-dir ./Datasets/en_te --output-dir ./backend/training/models/mt5-en-te-bilingual --direction both

## 4) Evaluate BLEU + chrF

python backend/training/evaluate_mt5_en_te.py --model-dir ./backend/training/models/mt5-en-te --dataset-dir ./Datasets/en_te --direction en-te

## 5) Hook Into Backend Routing

Set in backend/.env:

ENABLE_MT5_EN_TE_ROUTING=true
MT5_EN_TE_MODEL_PATH=./training/models/mt5-en-te

Routing behavior:
- en<->te -> mT5
- all other pairs -> MarianMT
- no direct pair in MarianMT -> pivot via English
