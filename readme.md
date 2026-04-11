# VideoTranslatorAI

> **Fully local AI pipeline** — Speech-to-Text via OpenAI Whisper + Text Translation via Google mT5. No external APIs. Runs entirely on CPU.

---

## Table of Contentstr

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Tech Stack](#tech-stack)
5. [AI Models](#ai-models)
6. [API Reference](#api-reference)
7. [Frontend Screens](#frontend-screens)
8. [Setup &amp; Installation](#setup--installation)
9. [Running the Application](#running-the-application)
10. [Accuracy Evaluation](#accuracy-evaluation)
11. [Supported Languages](#supported-languages)
12. [Performance Notes](#performance-notes)
13. [Model Architecture & Fine-Tuning Notes](#model-architecture--fine-tuning-notes)

---

## Overview

VideoTranslatorAI is a full-stack web application that:

- Accepts a **YouTube URL** or **uploaded audio/video file**
- **Transcribes** speech to text using OpenAI Whisper (auto language detection)
- **Translates** the transcription using Google's mT5 multilingual model — **no internet required after first model download**
- Displays results in a clean, step-by-step React UI with copy, download, and accuracy evaluation features

### Model Architecture & Fine-Tuning Notes

For complete documentation of Whisper architecture, mT5 architecture (general), fine-tuning guidance, and the exact model/data behavior currently implemented in this repository, see:

- [MODEL_ARCHITECTURE_AND_FINE_TUNING.md](MODEL_ARCHITECTURE_AND_FINE_TUNING.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Browser)                          │
│                  React + Vite  :5173                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP (REST)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend  :8000                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  POST /api/transcribe/          (YouTube URL)            │   │
│  │  POST /api/transcribe-file/     (File upload)            │   │
│  │  POST /api/translate/           (Text translation)       │   │
│  │  POST /api/evaluate-accuracy/   (WER / BLEU metrics)    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────┐   ┌─────────────────────────────────┐  │
│  │  YouTube Transcript │   │  yt-dlp + FFmpeg                │  │
│  │  API (fast path)    │   │  (audio extraction fallback)    │  │
│  └──────────┬──────────┘   └───────────────┬─────────────────┘  │
│             │                              │                    │
│             └──────────────┬───────────────┘                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │  OpenAI Whisper (base)  │  Speech → Text         │
│              │  CPU · Auto-detect lang │                        │
│              └─────────────┬───────────┘                        │
│                            │                                    │
│                            ▼                                    │
│              ┌─────────────────────────┐                        │
│              │  Google mT5-small       │  Text → Translation    │
│              │  CPU · Fully Offline    │                        │
│              └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
Input (URL or File)
       │
       ├─── YouTube URL? ──YES──► YouTube Transcript API (fast, no audio download)
       │                              │
       │                        transcript found?
       │                         YES │    NO │
       │                             │       └──► [fallback to audio path]
       │
       └─── File / fallback ──► yt-dlp downloads audio ──► FFmpeg extracts WAV
                                         │
                                         ▼
                               Whisper transcribes audio
                               (auto language detection)
                                         │
                                         ▼
                         Translation needed? (target ≠ source)
                              YES │         NO │
                                  ▼            └──► Return transcription only
                           mT5-small generates translation
                                  │
                                  ▼
                            API Response
              { transcription, translation, detected_language, status }
```

---

## Project Structure

```
VideoTranslatorAI/
├── backend/
│   ├── main.py                  # FastAPI app — all endpoints + AI models
│   ├── accuracy_evaluator.py    # WER / character accuracy helpers
│   ├── test_accuracy.py         # Accuracy test runner
│   ├── test_translation.py      # mT5 translation endpoint tests
│   ├── check_transcripts.py     # Transcript availability checker
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables (local only)
│   └── .env.example             # Env template (no secrets needed)
│
└── frontend/
    └── src/
        ├── App.jsx              # Root — step router + state management
        ├── main.jsx             # Vite entry point
        ├── App.css              # Global styles
        ├── index.css            # CSS reset / base
        ├── screens/
        │   ├── LandingScreen.jsx     # Step 1 — Welcome / hero
        │   ├── UploadScreen.jsx      # Step 2 — URL or file input
        │   ├── LanguageScreen.jsx    # Step 3 — Source/target language
        │   ├── ProcessingScreen.jsx  # Step 4 — Loading / progress
        │   └── ResultsScreen.jsx     # Step 5 — Transcription + translation
        ├── components/
        │   └── ProgressBar.jsx       # Step indicator bar
        └── utils/
            └── accuracyCalculator.js # Client-side accuracy scoring
```

---

## Tech Stack

### Backend

| Library                    | Version | Purpose               |
| -------------------------- | ------- | --------------------- |
| `fastapi`                | latest  | REST API framework    |
| `uvicorn`                | latest  | ASGI server           |
| `openai-whisper`         | latest  | Speech-to-text        |
| `transformers`           | ≥4.0   | mT5 model inference   |
| `torch`                  | latest  | PyTorch (CPU)         |
| `sentencepiece`          | latest  | mT5 tokenizer         |
| `yt-dlp`                 | latest  | Audio/video download  |
| `youtube-transcript-api` | latest  | YouTube caption fetch |
| `python-multipart`       | latest  | File upload support   |
| `jiwer`                  | latest  | WER metric            |
| `python-dotenv`          | latest  | Env var loading       |

### Frontend

| Library   | Version | Purpose                      |
| --------- | ------- | ---------------------------- |
| `react` | 18      | UI framework                 |
| `vite`  | 5       | Development server + bundler |

---

## AI Models

### 1. OpenAI Whisper (`base`)

| Property   | Value                                    |
| ---------- | ---------------------------------------- |
| Model size | ~145 MB                                  |
| Device     | CPU                                      |
| Languages  | 90+ (auto-detected)                      |
| Input      | WAV / MP3 / MP4 audio                    |
| Output     | Plain text transcription + language code |

**Whisper handles**: language auto-detection, Indian scripts (Telugu, Hindi, etc.), multi-accent English.

---

### 2. Google mT5-small

| Property          | Value                                      |
| ----------------- | ------------------------------------------ |
| Model size        | ~1.2 GB                                    |
| Device            | CPU only                                   |
| Framework         | HuggingFace Transformers                   |
| Tokenizer         | `T5Tokenizer` (SentencePiece)            |
| Languages         | 101 languages                              |
| Input format      | `translate {source} to {target}: {text}` |
| Max input tokens  | 512                                        |
| Max output tokens | 256                                        |
| Beam search       | 4 beams                                    |

**First launch**: model is downloaded from HuggingFace (~1.2 GB) and cached at `~/.cache/huggingface/`. All subsequent startups load instantly from disk.

---

## API Reference

### `POST /api/transcribe/`

Transcribe audio from a YouTube URL.

**Request**

```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "target_language": "te",
  "source_language": "en"
}
```

**Response**

```json
{
  "transcription": "Hello, this is a test...",
  "translation": "నమస్కారం, ఇది ఒక పరీక్ష...",
  "detected_language": "English",
  "language_code": "en",
  "target_language": "te",
  "status": "success_youtube_transcript"
}
```

| Status Value                      | Meaning                              |
| --------------------------------- | ------------------------------------ |
| `success_youtube_transcript`    | Used YouTube captions (fast path)    |
| `success_whisper_transcription` | Used Whisper on downloaded audio     |
| `error_translation_failed: ...` | Transcription OK, translation failed |

---

### `POST /api/transcribe-file/`

Upload an audio/video file directly.

**Request**: `multipart/form-data` with field `file`

**Response**: Same shape as `/api/transcribe/`

---

### `POST /api/translate/`

Translate arbitrary text using mT5.

**Request**

```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "te"
}
```

**Response**

```json
{
  "original_text": "Hello, how are you?",
  "translated_text": "నమస్కారం, మీరు ఎలా ఉన్నారు?",
  "source_language": "en",
  "target_language": "te",
  "status": "success"
}
```

---

### `POST /api/evaluate-accuracy/`

Calculate transcription/translation accuracy metrics.

**Request**

```json
{
  "reference_text": "Hello world this is a test",
  "predicted_text": "Hello world this is a test",
  "mode": "transcription"
}
```

**Response**

```json
{
  "overall_accuracy": 98.5,
  "wer": 0.05,
  "wer_percentage": 5.0,
  "character_accuracy": 99.2,
  "word_accuracy": 95.0,
  "quality_level": "Excellent",
  "reference_word_count": 6,
  "predicted_word_count": 6
}
```

| Quality Level | Overall Accuracy |
| ------------- | ---------------- |
| Excellent     | ≥ 95%           |
| Very Good     | ≥ 85%           |
| Good          | ≥ 75%           |
| Fair          | ≥ 60%           |
| Poor          | < 60%            |

---

## Frontend Screens

The UI is a **5-step wizard** with a persistent progress bar.

| Step | Screen               | Description                                                                   |
| ---- | -------------------- | ----------------------------------------------------------------------------- |
| 1    | `LandingScreen`    | Hero / welcome page, entry point                                              |
| 2    | `UploadScreen`     | Paste YouTube URL**or** upload a local file                             |
| 3    | `LanguageScreen`   | Pick source language (or Auto-detect) + target language                       |
| 4    | `ProcessingScreen` | Animated loading state while backend processes                                |
| 5    | `ResultsScreen`    | View transcription + translation, copy/download text, run accuracy evaluation |

---

## Setup & Installation

### Prerequisites

| Tool    | Minimum Version                                                 |
| ------- | --------------------------------------------------------------- |
| Python  | 3.9+                                                            |
| Node.js | 18+                                                             |
| npm     | 9+                                                              |
| FFmpeg  | any (optional — needed only if YouTube transcript unavailable) |

### 1. Clone the repository

```bash
git clone <repo-url>
cd VideoTranslatorAI
```

### 2. Backend setup

```powershell
cd backend

# Create and activate virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

> **First run** downloads `google/mt5-small` (~1.2 GB) from HuggingFace automatically.
> Model is cached locally — all subsequent starts are offline and instant.

### 3. Frontend setup

```powershell
cd frontend
npm install
```

### 4. Environment variables

No API keys are required. The `.env.example` in `backend/` confirms this:

```
# No external API keys required.
# Translation runs fully locally using google/mt5-small.
```

---

## Running the Application

### Start the Backend

```powershell
cd backend
python main.py
```

Expected startup output:

```
Loading Whisper base model...
Whisper model loaded successfully!
Loading mT5 translation model (google/mt5-small)...
mT5 model loaded successfully! Running on CPU.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Start the Frontend

```powershell
cd frontend
npm run dev
```

Expected output:

```
VITE v5.x  ready in 3000ms
➜  Local:   http://localhost:5173/
```

### Access the Application

| Service            | URL                         |
| ------------------ | --------------------------- |
| Frontend (UI)      | http://localhost:5173       |
| Backend API        | http://localhost:8000       |
| API Docs (Swagger) | http://localhost:8000/docs  |
| API Docs (ReDoc)   | http://localhost:8000/redoc |

---

## Accuracy Evaluation

The app includes a built-in accuracy evaluator available on the Results screen.

### Metrics Calculated

| Metric                       | Description                                                    |
| ---------------------------- | -------------------------------------------------------------- |
| **WER**                | Word Error Rate — industry standard for transcription quality |
| **Character Accuracy** | Levenshtein similarity at character level                      |
| **Word Accuracy**      | `100 - WER%`                                                 |
| **Overall Accuracy**   | `Character × 0.6 + Word × 0.4` (weighted)                  |

### Test Scripts

```powershell
# Test translation endpoint (server must be running)
python backend/test_translation.py

# Run accuracy evaluation suite
python backend/test_accuracy.py
```

---

## Supported Languages

The following language codes are accepted for `source_language` and `target_language`:

| Code   | Language | Code   | Language   |
| ------ | -------- | ------ | ---------- |
| `en` | English  | `hi` | Hindi      |
| `te` | Telugu   | `ta` | Tamil      |
| `kn` | Kannada  | `ml` | Malayalam  |
| `bn` | Bengali  | `gu` | Gujarati   |
| `mr` | Marathi  | `pa` | Punjabi    |
| `or` | Odia     | `as` | Assamese   |
| `ne` | Nepali   | `ur` | Urdu       |
| `zh` | Chinese  | `ja` | Japanese   |
| `ko` | Korean   | `ar` | Arabic     |
| `fr` | French   | `de` | German     |
| `es` | Spanish  | `pt` | Portuguese |
| `ru` | Russian  | `it` | Italian    |
| `tr` | Turkish  | `nl` | Dutch      |

> mT5-small supports 101 languages. Translation quality is best for high-resource languages (English, French, German, Spanish). For low-resource languages (Telugu, Kannada, etc.), results are functional but may be imperfect — mT5-small is a general-purpose model, not a dedicated translation model.

---

## Performance Notes

| Operation                            | Typical Time (CPU) |
| ------------------------------------ | ------------------ |
| Whisper transcription (1 min audio)  | 30–90 seconds     |
| mT5 translation (short text)         | 5–15 seconds      |
| mT5 translation (long text, chunked) | 15–60 seconds     |
| YouTube transcript fetch (fast path) | < 2 seconds        |

**Tips to improve speed:**

- Use YouTube URLs when possible — the transcript fast-path skips audio download and Whisper entirely
- Keep source text under 400 characters per chunk for optimal mT5 performance
- Run on a machine with more CPU cores or use GPU by changing `.to('cpu')` → `.to('cuda')` in `main.py`

---

## License

MIT
