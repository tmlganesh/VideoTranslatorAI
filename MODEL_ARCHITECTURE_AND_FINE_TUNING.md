# Model Architecture, Fine-Tuning, and Data Usage Notes

This document explains:
1. Which models are used in this project right now.
2. Whisper architecture (general).
3. mT5 architecture (general).
4. Fine-tuning approach for Whisper and mT5.
5. How this project currently uses data end-to-end.

## 1) What Is Actually Used In This Repository

Current backend behavior in backend/main.py:
- Speech-to-text: OpenAI Whisper base model (lazy-loaded, on-demand).
- Translation: Helsinki-NLP opus-mt models via MarianMTModel and MarianTokenizer.
- Translation strategy: direct pair translation when available, else pivot translation through English.
- Runtime mode: inference only (no training or fine-tuning code path in this repository).

Important clarification:
- Some README sections still mention mT5.
- Runtime translation code currently uses Marian/opus-mt models, not mT5.

## 2) Whisper Architecture (General)

Whisper is a Transformer encoder-decoder ASR model trained on large-scale weakly supervised multilingual audio-text data.

High-level pipeline:
1. Audio waveform -> log-Mel spectrogram features.
2. Encoder consumes acoustic features and builds contextual speech representation.
3. Decoder autoregressively generates tokens (text, timestamps, and language/task tokens).

Core architectural points:
- Family: sequence-to-sequence Transformer.
- Input representation: 80-channel log-Mel spectrogram frames.
- Typical inference window: around 30-second audio segments.
- Multilingual and multitask token setup: language and task are guided via special tokens.
- Output types: transcribed text, optional timestamps, detected language signal.

Why Whisper is strong:
- Robust to accents/noise relative to many older ASR baselines.
- Good multilingual transfer due to broad pretraining data.
- Works well for zero-shot transcription in many languages.

Whisper base variant (commonly used facts):
- Approx parameter count: ~74M.
- Good balance of speed and quality for CPU/GPU mixed environments.

## 3) mT5 Architecture (General)

mT5 is a multilingual Text-to-Text Transfer Transformer (encoder-decoder) trained with a span corruption objective on multilingual web text.

High-level pipeline:
1. Input text is tokenized with SentencePiece.
2. Encoder builds a multilingual semantic representation.
3. Decoder generates output text token-by-token (translation, summarization, QA, etc.).

Core architectural points:
- Family: T5-style encoder-decoder Transformer.
- Training paradigm: text-to-text for all tasks.
- Pretraining objective: span corruption denoising.
- Tokenization: shared multilingual SentencePiece vocabulary.
- Typical prompt style for translation: "translate <src_lang> to <tgt_lang>: <text>".

Common model scale reference:
- mT5-small: about 300M parameters.
- Larger mT5 variants increase quality but also memory/latency cost.

mT5 strengths and limits:
- Strength: one model can handle many languages/tasks.
- Limit: for production translation quality, dedicated MT models can outperform mT5 on specific language pairs.

## 4) Fine-Tuning Guidance

This repository currently does not fine-tune models. It only runs inference.

### 4.1 Whisper Fine-Tuning (General Approach)

Goal:
- Adapt ASR quality for domain-specific terms, accents, or low-resource language conditions.

Data you need:
- Paired audio + transcript.
- Metadata fields typically include:
  - audio_path
  - transcript
  - language
  - optional speaker/domain tags

Data preparation:
1. Resample to 16 kHz mono.
2. Normalize loudness and trim long silence where appropriate.
3. Keep transcript normalization policy consistent (punctuation/casing/numerals).
4. Split train/validation/test by speaker or source domain (avoid leakage).

Training options:
- Full fine-tuning of all parameters.
- Parameter-efficient tuning (LoRA/adapters) to reduce compute and memory.

Evaluation:
- WER/CER as primary metrics.
- Also inspect domain terminology accuracy manually.

### 4.2 mT5 Fine-Tuning (General Approach)

Goal:
- Improve translation quality for your language pairs/domain (for example, technical or medical text).

Data you need:
- Parallel corpus with source-target sentence pairs.
- Typical schema:
  - source_text
  - target_text
  - source_language
  - target_language

Data preparation:
1. Clean misaligned pairs.
2. Remove duplicates and corrupted rows.
3. Normalize script/punctuation conventions consistently.
4. Keep sentence lengths reasonable; optionally bucket by length.

Training formulation:
- Input: "translate <source_language> to <target_language>: <source_text>"
- Target: <target_text>
- Loss: token-level cross-entropy on decoder outputs.

Evaluation:
- Automatic metrics: BLEU, chrF, COMET (if available).
- Human checks: adequacy, fluency, terminology fidelity.

Practical note:
- For strict translation workloads, dedicated MT models (Marian/NLLB/M2M style) are often preferred over general-purpose mT5.

## 5) How Data Is Used In This Project (Current Implementation)

### 5.1 Input Modes

The backend supports two input paths:
1. YouTube URL path:
- Try YouTube transcript API first (fast path, no audio download).
- If transcript is unavailable, fall back to audio download and Whisper transcription.

2. File upload path:
- Accept uploaded media/audio file and run Whisper transcription.

### 5.2 Transcription Stage

- Whisper base is loaded lazily (first use only).
- Language is auto-detected during transcription.
- Small language-specific post-processing exists (for example Telugu cleanup).

### 5.3 Translation Stage

- Language codes are normalized (for example en-US -> en).
- If source and target are same, translation is skipped.
- If direct opus-mt model exists for pair: use direct translation.
- If no direct pair and both sides are non-English: pivot through English.
- Multilingual model prefixes are applied when needed (for example >>tel<<).

### 5.4 Text Chunking And Generation

- Long text is split into short chunks (about 200 characters) for better translation quality.
- Translation uses beam search generation settings in Marian models.
- Basic output quality guards exist:
  - empty output fallback
  - degenerate repetition detection
  - identical-source checks

### 5.5 Caching And Runtime

- Translation models are loaded on demand and cached in memory per language pair.
- This reduces repeated model load overhead after first call.
- Entire current pipeline is inference-time only; no training data is persisted for model updates.

## 6) Fine-Tuning Status In This Project

Current status:
- No fine-tuning pipeline is implemented.
- No training loop, checkpoint saving, or trainer scripts are present.
- User inputs are processed for immediate inference response only.

If you want fine-tuning in this repository later, add:
1. Data ingestion and curation scripts.
2. Dedicated training pipeline (Whisper or mT5 or both).
3. Evaluation suite with held-out test sets.
4. Model registry/versioning and rollback strategy.

## 7) Documentation Summary

Short summary for stakeholders:
- Current production path in this codebase: Whisper (ASR) + opus-mt Marian (translation), fully local inference.
- mT5 section in this document is architectural guidance and future-option context, not current runtime implementation.
- Fine-tuning is not currently performed; data is used for real-time inference only.

## 8) Execution-Ready Implementation (Now Added)

The repository now includes an offline training pipeline and hybrid routing implementation:

- Offline pipeline folder: backend/training/
- Dataset build script: backend/training/prepare_en_te_dataset.py
- Training script: backend/training/train_mt5_en_te.py
- Evaluation script: backend/training/evaluate_mt5_en_te.py
- Training dependencies: backend/training/requirements.txt

### 8.1 Build Dataset (70/30 Samanantar + OpenSubtitles)

1. Install training dependencies:

  python -m pip install -r backend/training/requirements.txt

2. Run dataset preparation:

  python backend/training/prepare_en_te_dataset.py --output-dir Datasets/en_te --target-pairs 200000 --max-tokens 128

This enforces:
- 70% Samanantar + 30% OpenSubtitles
- cleaning (empty/misaligned/duplicate/too-long removal)
- spoken-style prioritization
- unified schema and mT5 prompt-format exports

### 8.2 Train mT5

Phase 1 (EN->TE baseline):

python backend/training/train.py --dataset-dir Datasets/en_te --output-dir backend/training/models/mt5-en-te --direction en-te

Phase 2 optional (EN<->TE):

python backend/training/train.py --dataset-dir Datasets/en_te --output-dir backend/training/models/mt5-en-te-bilingual --direction both

### 8.3 Evaluate

python backend/training/evaluate_mt5_en_te.py --model-dir backend/training/models/mt5-en-te --dataset-dir Datasets/en_te --direction en-te

### 8.4 Backend Routing Configuration

Set these in backend/.env:

- ENABLE_MT5_EN_TE_ROUTING=true
- MT5_EN_TE_MODEL_PATH=backend/training/models/mt5-en-te
- MT5_MAX_SOURCE_TOKENS=256
- MT5_MAX_TARGET_TOKENS=256

Routing behavior in backend:
- en<->te -> mT5
- all other language pairs -> MarianMT
- no direct Marian pair -> pivot via English
