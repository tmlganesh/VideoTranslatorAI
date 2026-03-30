from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import yt_dlp
import whisper
import os
import tempfile
import uvicorn
import shutil
import glob
import re
import json
import time
import torch
from transformers import MarianMTModel, MarianTokenizer
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_ffmpeg_path():
    """Find and setup FFmpeg path"""
    possible_paths = [
        r"C:\Tools\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe"
    ]
    
    # Check WinGet installation path
    winget_pattern = r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_*\ffmpeg*\bin\ffmpeg.exe"
    winget_paths = glob.glob(winget_pattern)
    if winget_paths:
        possible_paths.extend(winget_paths)
    
    for path in possible_paths:
        if os.path.exists(path):
            ffmpeg_dir = os.path.dirname(path)
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path:
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
            print(f"FFmpeg found and added to PATH: {ffmpeg_dir}")
            return ffmpeg_dir
    
    print("FFmpeg not found in common locations")
    return None

# Setup FFmpeg on module import
FFMPEG_PATH = setup_ffmpeg_path()

# Load Whisper model once at startup
print("Loading Whisper base model...")
model = whisper.load_model("base")  # Smaller, faster model for development
print("Whisper model loaded successfully!")

# Cache for Helsinki-NLP opus-mt translation models (loaded on-demand)
_translation_model_cache = {}

# Helsinki-NLP opus-mt language code mapping
# Maps (source_lang, target_lang) → model name
# Models are purpose-built bilingual or multilingual Marian-MT transformers
OPUS_MT_MODEL_MAP = {
    # --- Indian languages → English ---
    ('te', 'en'): 'Helsinki-NLP/opus-mt-te-en',
    ('hi', 'en'): 'Helsinki-NLP/opus-mt-hi-en',
    ('ta', 'en'): 'Helsinki-NLP/opus-mt-dra-en',   # Dravidian → English
    ('kn', 'en'): 'Helsinki-NLP/opus-mt-dra-en',
    ('ml', 'en'): 'Helsinki-NLP/opus-mt-dra-en',
    ('bn', 'en'): 'Helsinki-NLP/opus-mt-bn-en',
    ('ur', 'en'): 'Helsinki-NLP/opus-mt-ur-en',
    ('mr', 'en'): 'Helsinki-NLP/opus-mt-mr-en',
    # --- English → Indian languages ---
    ('en', 'hi'): 'Helsinki-NLP/opus-mt-en-hi',     # Dedicated en→hi model
    ('en', 'te'): 'Helsinki-NLP/opus-mt-en-dra',    # Dravidian family (needs >>tel<< prefix)
    ('en', 'ta'): 'Helsinki-NLP/opus-mt-en-dra',    # (needs >>tam<< prefix)
    ('en', 'kn'): 'Helsinki-NLP/opus-mt-en-dra',    # (needs >>kan<< prefix)
    ('en', 'ml'): 'Helsinki-NLP/opus-mt-en-dra',    # (needs >>mal<< prefix)
    ('en', 'bn'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>ben<< prefix)
    ('en', 'ur'): 'Helsinki-NLP/opus-mt-en-ur',
    ('en', 'mr'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>mar<< prefix)
    ('en', 'gu'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>guj<< prefix)
    ('en', 'pa'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>pan<< prefix)
    ('en', 'as'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>asm<< prefix)
    ('en', 'ne'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>nep<< prefix)
    ('en', 'od'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>ori<< prefix)
    # --- European languages ---
    ('fr', 'en'): 'Helsinki-NLP/opus-mt-fr-en',
    ('en', 'fr'): 'Helsinki-NLP/opus-mt-en-fr',
    ('de', 'en'): 'Helsinki-NLP/opus-mt-de-en',
    ('en', 'de'): 'Helsinki-NLP/opus-mt-en-de',
    ('es', 'en'): 'Helsinki-NLP/opus-mt-es-en',
    ('en', 'es'): 'Helsinki-NLP/opus-mt-en-es',
    ('pt', 'en'): 'Helsinki-NLP/opus-mt-pt-en',
    ('en', 'pt'): 'Helsinki-NLP/opus-mt-en-pt',
    ('it', 'en'): 'Helsinki-NLP/opus-mt-it-en',
    ('en', 'it'): 'Helsinki-NLP/opus-mt-en-it',
    ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
    ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-ru',
    ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
    ('en', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
    ('ja', 'en'): 'Helsinki-NLP/opus-mt-ja-en',
    ('en', 'ja'): 'Helsinki-NLP/opus-mt-en-jap',
    ('ar', 'en'): 'Helsinki-NLP/opus-mt-ar-en',
    ('en', 'ar'): 'Helsinki-NLP/opus-mt-en-ar',
    ('ko', 'en'): 'Helsinki-NLP/opus-mt-ko-en',
    ('en', 'ko'): 'Helsinki-NLP/opus-mt-en-mul',    # (needs >>kor<< prefix)
    ('tr', 'en'): 'Helsinki-NLP/opus-mt-tr-en',
    ('en', 'tr'): 'Helsinki-NLP/opus-mt-en-trk',
}

# Language prefix tokens required by multilingual models (en-dra, en-mul, dra-en)
# These tokens MUST be prepended to SOURCE text for the model to know the target language.
# Format: >>three_letter_code<<
# Only needed for models that handle multiple target languages.
LANG_PREFIX_MAP = {
    # en-dra targets (Dravidian family)
    ('en', 'te'): '>>tel<< ',
    ('en', 'ta'): '>>tam<< ',
    ('en', 'kn'): '>>kan<< ',
    ('en', 'ml'): '>>mal<< ',
    # en-mul targets
    ('en', 'bn'): '>>ben<< ',
    ('en', 'mr'): '>>mar<< ',
    ('en', 'gu'): '>>guj<< ',
    ('en', 'pa'): '>>pan<< ',
    ('en', 'as'): '>>asm<< ',
    ('en', 'ne'): '>>nep<< ',
    ('en', 'od'): '>>ori<< ',
    ('en', 'ko'): '>>kor<< ',
    # dra-en sources (some dra-en models may need source prefix)
    # Usually bilingual dra→en models auto-detect, but if needed:
    # ('ta', 'en'): '>>eng<< ',
}

def get_translation_model(source_lang: str, target_lang: str):
    """
    Load (or retrieve from cache) the appropriate Helsinki-NLP opus-mt model
    for the given language pair. Raises ValueError if no model is found.
    """
    pair = (source_lang, target_lang)
    if pair in _translation_model_cache:
        return _translation_model_cache[pair]

    model_name = OPUS_MT_MODEL_MAP.get(pair)
    if not model_name:
        # Generic fallback: try a direct bilingual model name
        if target_lang == 'en':
            model_name = f'Helsinki-NLP/opus-mt-{source_lang}-en'
        elif source_lang == 'en':
            model_name = 'Helsinki-NLP/opus-mt-en-mul'
        else:
            raise ValueError(
                f"No translation model available for {source_lang}→{target_lang}. "
                f"Will attempt pivot translation through English."
            )

    print(f"Loading translation model: {model_name}")
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    mt_model = MarianMTModel.from_pretrained(model_name)
    mt_model.eval()
    _translation_model_cache[pair] = (tokenizer, mt_model, model_name)
    print(f"Translation model loaded: {model_name}")
    return tokenizer, mt_model, model_name

print("Helsinki-NLP opus-mt translation models will be loaded on-demand (first use).")

def extract_youtube_video_id(url):
    """Extract YouTube video ID from various YouTube URL formats."""
    youtube_regex = re.compile(
        r'(?:https?://)?' # protocol
        r'(?:www\.)?' # www
        r'(?:youtube\.com/(?:watch\?v=|embed/|v/)|youtu\.be/)' # domain and path
        r'([^&\n?#]+)' # video ID
    )
    match = youtube_regex.search(url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id, source_language=None):
    """
    Try to fetch YouTube transcript using YouTube Transcript API.
    Prioritizes the original language (auto-generated) first, then manual transcripts.
    Returns tuple: (transcript_text, detected_language_code, detected_language_name)
    """
    try:
        # Initialize YouTube Transcript API
        ytt_api = YouTubeTranscriptApi()
        
        # Get available transcripts
        transcript_list = ytt_api.list(video_id)
        
        # Enhanced language mapping with more regional languages
        language_names = {
            'en': 'English', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'kn': 'Kannada',
            'ml': 'Malayalam', 'bn': 'Bengali', 'gu': 'Gujarati', 'mr': 'Marathi', 'pa': 'Punjabi',
            'ur': 'Urdu', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
            'fr': 'French', 'de': 'German', 'es': 'Spanish', 'pt': 'Portuguese', 'ru': 'Russian',
            'it': 'Italian', 'tr': 'Turkish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 
            'no': 'Norwegian', 'or': 'Odia', 'as': 'Assamese', 'ne': 'Nepali', 'si': 'Sinhala'
        }
        
        transcript = None
        selected_lang = None
        
        # If user specified a source language, try that first
        if source_language and source_language != 'Auto-detect':
            lang_code_map = {
                'English': 'en', 'Hindi': 'hi', 'Telugu': 'te', 'Tamil': 'ta',
                'Kannada': 'kn', 'Malayalam': 'ml', 'Bengali': 'bn', 'Gujarati': 'gu',
                'Marathi': 'mr', 'Spanish': 'es', 'French': 'fr', 'German': 'de'
            }
            preferred_lang = lang_code_map.get(source_language, source_language.lower()[:2])
            try:
                transcript = transcript_list.find_transcript([preferred_lang]).fetch()
                selected_lang = preferred_lang
                print(f"Found transcript in user-specified language: {source_language}")
            except:
                print(f"No transcript found for specified language: {source_language}")
        
        # Priority 1: Get auto-generated transcript (original language of the video)
        if not transcript:
            try:
                for t in transcript_list:
                    if t.is_generated:
                        transcript = t.fetch()
                        selected_lang = t.language_code
                        print(f"Found auto-generated transcript in original language: {selected_lang}")
                        break
            except Exception as e:
                print(f"No auto-generated transcript: {e}")
        
        # Priority 2: Try English manual transcript (common for TED talks)
        if not transcript:
            try:
                transcript = transcript_list.find_transcript(['en']).fetch()
                selected_lang = 'en'
                print(f"Found English transcript")
            except:
                pass
        
        # Priority 3: Try any available manual transcript
        if not transcript:
            try:
                for t in transcript_list:
                    if not t.is_generated:
                        transcript = t.fetch()
                        selected_lang = t.language_code
                        print(f"Found manual transcript in: {selected_lang}")
                        break
            except:
                pass
        
        if transcript:
            # Build transcript text preserving sentence boundaries
            # Each snippet from the YouTube API is a caption segment
            segments = []
            for snippet in transcript:
                text_part = snippet.text if hasattr(snippet, 'text') else str(snippet)
                text_part = text_part.strip()
                if text_part:
                    segments.append(text_part)
            
            if segments:
                # Join with sentence-preserving separator (period + space)
                # so _split_into_chunks can split on sentence boundaries
                transcript_text = '. '.join(segments)
                # Clean up double periods / extra whitespace
                transcript_text = re.sub(r'\.\s*\.', '.', transcript_text)
                transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
            else:
                # Fallback to formatter if segment extraction failed
                formatter = TextFormatter()
                transcript_text = formatter.format_transcript(transcript)
                transcript_text = re.sub(r'\s+', ' ', transcript_text).strip()
            
            # Get language name
            detected_language_name = language_names.get(selected_lang, selected_lang.upper())
            
            print(f"YouTube transcript found: {detected_language_name} ({selected_lang})")
            print(f"Transcript length: {len(transcript_text)} characters")
            print(f"Segments count: {len(segments)}")
            
            return transcript_text, selected_lang, detected_language_name
        
    except Exception as e:
        print(f"YouTube transcript fetch failed: {str(e)}")
    
    return None, None, None

def improve_telugu_transcription(text, language_code):
    """
    Post-process Telugu transcription to improve accuracy.
    """
    if language_code != 'te':
        return text
    
    # Telugu-specific improvements
    replacements = {
        # Common Telugu transcription fixes
        'అవునా': 'అవును',
        'ఎలా': 'ఎలా',
        'ఎవరు': 'ఎవరు',
        'ఎక్కడ': 'ఎక్కడ',
        'ఎప్పుడు': 'ఎప్పుడు',
        'ఏమిటి': 'ఏమిటి',
        'మంచిది': 'మంచిది',
        'చెప్పు': 'చెప్పు',
        'వినండి': 'వినండి',
        'చూడండి': 'చూడండి',
        # Add more common Telugu word corrections
    }
    
    # Apply replacements
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    
    # Clean up spacing around Telugu punctuation
    import re
    text = re.sub(r'\s+([।॥])', r'\1', text)  # Remove space before devanagari punctuation
    text = re.sub(r'([।॥])\s*', r'\1 ', text)  # Ensure single space after punctuation
    
    return text.strip()

def _split_into_chunks(text: str, max_chunk_chars: int = 200) -> list:
    """
    Split text into sentence-level chunks that stay within max_chunk_chars.
    Marian models work best with individual sentences or very short paragraphs.
    Smaller chunks (200 chars) produce significantly better translations.
    """
    if len(text) <= max_chunk_chars:
        return [text]

    # Split on sentence-ending punctuation (English, Hindi/Devanagari, pipes, newlines)
    sentences = re.split(r'(?<=[.!?|।\n])\s*', text)
    text_chunks = []
    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                text_chunks.append(current_chunk.strip())
            if len(sentence) > max_chunk_chars:
                # For very long sentences, split on commas or clause boundaries
                sub_parts = re.split(r'(?<=[,;:])\s*', sentence)
                sub_chunk = ""
                for part in sub_parts:
                    part = part.strip()
                    if not part:
                        continue
                    if len(sub_chunk) + len(part) + 1 <= max_chunk_chars:
                        sub_chunk += part + " "
                    else:
                        if sub_chunk:
                            text_chunks.append(sub_chunk.strip())
                        # If a single part is still too long, hard-split it
                        if len(part) > max_chunk_chars:
                            for i in range(0, len(part), max_chunk_chars):
                                text_chunks.append(part[i:i + max_chunk_chars])
                            sub_chunk = ""
                        else:
                            sub_chunk = part + " "
                if sub_chunk:
                    text_chunks.append(sub_chunk.strip())
                current_chunk = ""
            else:
                current_chunk = sentence + " "
    if current_chunk:
        text_chunks.append(current_chunk.strip())
    return text_chunks if text_chunks else [text]


def _translate_direct(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text directly using a single opus-mt model.
    Handles language prefix tokens for multilingual models automatically.
    """
    tokenizer, mt_model, model_name = get_translation_model(source_lang, target_lang)

    # Check if this language pair needs a prefix token for the target language
    prefix = LANG_PREFIX_MAP.get((source_lang, target_lang), '')
    if prefix:
        print(f"  Using language prefix: {prefix.strip()}")

    text_chunks = _split_into_chunks(text)
    print(f"  Translating {len(text_chunks)} chunk(s) with {model_name}...")
    translated_chunks = []

    translation_start = time.time()
    for i, chunk in enumerate(text_chunks):
        # Prepend the language prefix token if required by this model
        input_text = prefix + chunk if prefix else chunk

        inputs = tokenizer(
            [input_text],
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        )
        with torch.no_grad():
            outputs = mt_model.generate(
                **inputs,
                max_length=512,
                num_beams=5,
                length_penalty=1.0,
                early_stopping=True
            )
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Quality validation: detect degenerate translations
        decoded_clean = decoded.strip()
        chunk_clean = chunk.strip()
        is_valid = True

        # Check 1: translation is empty
        if not decoded_clean:
            print(f"  WARNING: Chunk {i+1} produced empty translation, keeping source")
            is_valid = False

        # Check 2: translation identical to source (model copied input)
        if is_valid and decoded_clean == chunk_clean:
            print(f"  WARNING: Chunk {i+1} translation identical to source, keeping as-is")
            # Still use it — might be proper nouns or numbers

        # Check 3: detect excessive repetition (degenerate output)
        if is_valid and len(decoded_clean) > 20:
            words = decoded_clean.split()
            if len(words) > 4:
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.15:  # Less than 15% unique words = likely degenerate
                    print(f"  WARNING: Chunk {i+1} has degenerate repetition (unique ratio: {unique_ratio:.2f}), keeping source")
                    is_valid = False

        translated_chunks.append(decoded_clean if is_valid else chunk_clean)
        print(f"  Chunk {i+1}/{len(text_chunks)}: {(decoded_clean if is_valid else chunk_clean)[:80]}")

    translation_time = time.time() - translation_start
    print(f"  Direct translation completed in {translation_time:.2f}s")
    return ' '.join(translated_chunks)


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text using Helsinki-NLP/opus-mt models (purpose-built for translation).
    Models are loaded on-demand and cached. Runs entirely on CPU with no external API calls.

    For non-English↔non-English pairs (e.g., Telugu→Hindi), automatically performs
    pivot translation through English: source→English→target.
    """
    print(f"=== opus-mt TRANSLATION ===")
    print(f"Source: {source_lang} → Target: {target_lang}")
    print(f"Text length: {len(text)} characters")

    # Same language — no translation needed
    if source_lang == target_lang:
        print("Source and target languages are the same. Skipping translation.")
        return text

    try:
        # Try direct translation first
        try:
            result = _translate_direct(text, source_lang, target_lang)
            print(f"=== Direct translation successful ===")
            return result
        except ValueError:
            # No direct model → pivot through English
            if source_lang != 'en' and target_lang != 'en':
                print(f"No direct model for {source_lang}→{target_lang}. "
                      f"Pivoting through English: {source_lang}→en→{target_lang}")
                # Step 1: source → English
                english_text = _translate_direct(text, source_lang, 'en')
                print(f"Pivot step 1 done ({source_lang}→en): {english_text[:100]}...")
                # Step 2: English → target
                result = _translate_direct(english_text, 'en', target_lang)
                print(f"Pivot step 2 done (en→{target_lang}): {result[:100]}...")
                print(f"=== Pivot translation successful ===")
                return result
            else:
                raise

    except ValueError as e:
        print(f"Translation model error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"opus-mt translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")

def try_api_video_transcription(video_url, api_key=None):
    """
    Optional integration with api.video for professional transcription.
    This requires an api.video API key and is used as a premium fallback.
    Returns tuple: (transcript_text, language_code, language_name, success)
    """
    if not api_key:
        return None, None, None, False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Create video with transcription enabled
        video_data = {
            'title': 'Transcription Job',
            'source': video_url,
            'transcript': True,
            'language': 'te'  # Prioritize Telugu
        }
        
        # Create video
        response = requests.post(
            'https://ws.api.video/videos',
            headers=headers,
            json=video_data,
            timeout=30
        )
        
        if response.status_code == 201:
            video_info = response.json()
            video_id = video_info.get('videoId')
            
            print(f"api.video: Video created with ID: {video_id}")
            
            # Note: In real implementation, you'd need to poll for transcription completion
            # and then fetch the transcript. This is a simplified version.
            return None, None, None, False  # Placeholder for now
            
    except Exception as e:
        print(f"api.video transcription failed: {str(e)}")
    
    return None, None, None, False

app = FastAPI(title="Video Transcription API", version="1.0.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React dev server port
        "http://10.10.182.57:5173",  # Network IP access
        "http://127.0.0.1:5173",  # Alternative localhost
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptionRequest(BaseModel):
    video_url: str
    target_language: Optional[str] = None  # Optional translation target language
    source_language: Optional[str] = None  # Optional source language hint

class TranscriptionResponse(BaseModel):
    transcription: str
    detected_language: str
    language_code: str
    status: str
    translation: str = ""
    target_language: str = ""

class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    status: str

@app.get("/")
async def root():
    return {"message": "Video Transcription API is running"}

@app.post("/api/transcribe/", response_model=TranscriptionResponse)
async def transcribe_video(request: TranscriptionRequest):
    """
    Transcribe audio from a video URL using YouTube Transcript API first (for speed), 
    then fallback to yt-dlp and whisper with language detection.
    """
    try:
        print(f"=== TRANSCRIPTION REQUEST DEBUG ===")
        print(f"Video URL: {request.video_url}")
        print(f"Target Language: {request.target_language}")
        print(f"Source Language: {request.source_language}")
        print(f"===================================")
        
        # Check if it's a YouTube URL and try to get existing transcript first
        video_id = extract_youtube_video_id(request.video_url)
        
        if video_id:
            print(f"YouTube video detected (ID: {video_id}). Trying to fetch existing transcript...")
            transcript_text, lang_code, lang_name = get_youtube_transcript(video_id, request.source_language)
            
            if transcript_text:
                print("Successfully retrieved YouTube transcript! Skipping audio processing.")
                
                # Handle translation if requested
                translation_text = None
                target_lang = None
                print(f"=== TRANSLATION ATTEMPT DEBUG ===")
                print(f"Request target language: '{request.target_language}'")
                print(f"Source language detected: '{lang_code}'")
                print(f"=================================")
                
                # Determine if translation is needed
                # Auto-translate to English if source is non-English and no target specified
                effective_target = request.target_language
                if (not effective_target or effective_target == "Same as Original (No Translation)") and lang_code != 'en':
                    effective_target = 'en'  # Auto-translate non-English to English
                    print(f"Auto-translating from {lang_code} to English (no target specified)")
                
                if effective_target and effective_target != "Same as Original (No Translation)" and effective_target != lang_code:
                    try:
                        print(f"Starting opus-mt translation from {lang_code} to {effective_target}")
                        print(f"Transcript text (first 200 chars): {transcript_text[:200]}...")
                        translation_text = translate_text(
                            text=transcript_text,
                            source_lang=lang_code,
                            target_lang=effective_target
                        )
                        print(f"Translation result (first 200 chars): {translation_text[:200]}...")
                        target_lang = effective_target
                        print(f"Translation completed for YouTube transcript")
                    except Exception as e:
                        print(f"Translation failed for YouTube transcript: {str(e)}")
                        # Return error status instead of silently failing
                        return TranscriptionResponse(
                            transcription=transcript_text,
                            detected_language=lang_name,
                            language_code=lang_code,
                            status=f"error_translation_failed: {str(e)}",
                            translation="",
                            target_language=""
                        )
                
                return TranscriptionResponse(
                    transcription=transcript_text,
                    detected_language=lang_name,
                    language_code=lang_code,
                    status="success_youtube_transcript",
                    translation=translation_text or "",
                    target_language=target_lang or ""
                )
            else:
                print("No YouTube transcript available. Falling back to audio processing...")
        
        # Create a temporary directory for audio files
        temp_dir = tempfile.mkdtemp()
        temp_audio_path = os.path.join(temp_dir, "temp_audio.%(ext)s")
        
        # Configure yt-dlp options for audio extraction
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': temp_audio_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # Use WAV instead of MP3 for better compatibility
                'preferredquality': '192',
            }],
            'extract_flat': False,
        }
        
        # Add FFmpeg location if found
        if FFMPEG_PATH:
            ydl_opts['ffmpeg_location'] = FFMPEG_PATH
        
        print(f"Downloading audio from: {request.video_url}")
        
        # Extract audio using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.video_url])
        
        # Find the extracted audio file (it will have .wav extension after processing)
        audio_file_path = os.path.join(temp_dir, "temp_audio.wav")
        
        if not os.path.exists(audio_file_path):
            raise HTTPException(status_code=500, detail="Failed to extract audio from video")
        
        print("Loading audio for language detection...")
        
        try:
            # Load audio and detect language
            audio = whisper.load_audio(audio_file_path)
            print(f"Audio loaded, shape: {audio.shape if hasattr(audio, 'shape') else 'unknown'}")
            
            audio = whisper.pad_or_trim(audio)
            print(f"Audio after padding/trimming, shape: {audio.shape if hasattr(audio, 'shape') else 'unknown'}")
            
            # Transcribe with automatic language detection — log latency
            transcribe_start = time.time()
            result = model.transcribe(audio_file_path, language=None)
            transcribe_time = time.time() - transcribe_start
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
            print(f"Direct transcription successful. Language: {detected_language_code} | Time: {transcribe_time:.2f}s")
            
        except Exception as lang_detect_error:
            print(f"Language detection failed: {lang_detect_error}")
            print("Falling back to direct transcription without language detection...")
            
            # Fallback: direct transcription
            transcribe_start = time.time()
            result = model.transcribe(audio_file_path)
            transcribe_time = time.time() - transcribe_start
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
            print(f"Fallback transcription done in {transcribe_time:.2f}s")
        
        # Get language name
        language_names = {
            'en': 'English', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'kn': 'Kannada',
            'ml': 'Malayalam', 'bn': 'Bengali', 'gu': 'Gujarati', 'mr': 'Marathi', 'pa': 'Punjabi',
            'ur': 'Urdu', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
            'fr': 'French', 'de': 'German', 'es': 'Spanish', 'pt': 'Portuguese', 'ru': 'Russian',
            'it': 'Italian', 'tr': 'Turkish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 
            'no': 'Norwegian', 'or': 'Odia', 'as': 'Assamese', 'ne': 'Nepali', 'si': 'Sinhala'
        }
        
        detected_language_name = language_names.get(detected_language_code, detected_language_code.upper())
        
        print(f"Detected language: {detected_language_name} ({detected_language_code})")
        print(f"Transcription completed: {transcription_text[:100]}...")
        
        # Apply language-specific improvements
        transcription_text = improve_telugu_transcription(transcription_text, detected_language_code)
        
        print(f"Transcription completed: {transcription_text[:100]}...")
        
        # Handle translation if requested
        translation_text = None
        target_lang = None
        
        # Determine if translation is needed
        # Auto-translate to English if source is non-English and no target specified
        effective_target = request.target_language
        if (not effective_target or effective_target == "Same as Original (No Translation)") and detected_language_code != 'en':
            effective_target = 'en'  # Auto-translate non-English to English
            print(f"Auto-translating from {detected_language_code} to English (no target specified)")
        
        if effective_target and effective_target != "Same as Original (No Translation)" and effective_target != detected_language_code:
            try:
                translation_text = translate_text(
                    text=transcription_text,
                    source_lang=detected_language_code,
                    target_lang=effective_target
                )
                target_lang = effective_target
                print(f"opus-mt translation completed for video transcription")
            except Exception as e:
                print(f"Translation failed for video transcription: {str(e)}")
                # Clean up and return error status
                shutil.rmtree(temp_dir, ignore_errors=True)
                return TranscriptionResponse(
                    transcription=transcription_text,
                    detected_language=detected_language_name,
                    language_code=detected_language_code,
                    status=f"error_translation_failed: {str(e)}",
                    translation="",
                    target_language=""
                )
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return TranscriptionResponse(
            transcription=transcription_text,
            detected_language=detected_language_name,
            language_code=detected_language_code,
            status="success_whisper_transcription",
            translation=translation_text or "",
            target_language=target_lang or ""
        )
    
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        
        # Clean up temporary directory in case of error
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/translate/", response_model=TranslationResponse)
async def translate_endpoint(request: TranslationRequest):
    """
    Translate text using local Helsinki-NLP/opus-mt models.
    Fully offline — no external API calls. Supports all major languages.
    """
    try:
        print(f"Translation request: {request.source_language} -> {request.target_language}")
        print(f"Text to translate: {request.text[:100]}...")

        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to translate cannot be empty")

        # Local mT5 translation (synchronous, CPU-only)
        translated_text = translate_text(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )

        print(f"Translation completed: {translated_text[:100]}...")

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


# Accuracy Evaluation Models
class AccuracyRequest(BaseModel):
    reference_text: str
    predicted_text: str
    mode: Optional[str] = "transcription"  # "transcription" or "translation"

class AccuracyResponse(BaseModel):
    overall_accuracy: float
    wer: float
    wer_percentage: float
    character_accuracy: float
    word_accuracy: float
    quality_level: str
    reference_word_count: int
    predicted_word_count: int


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def calculate_accuracy_metrics(reference: str, predicted: str):
    """Calculate various accuracy metrics between reference and predicted text."""
    # Normalize texts
    ref_normalized = ' '.join(reference.lower().split())
    pred_normalized = ' '.join(predicted.lower().split())
    
    # Character-level Levenshtein similarity
    char_distance = levenshtein_distance(ref_normalized, pred_normalized)
    max_len = max(len(ref_normalized), len(pred_normalized))
    character_accuracy = ((max_len - char_distance) / max_len * 100) if max_len > 0 else 100.0
    
    # Word-level metrics
    ref_words = ref_normalized.split()
    pred_words = pred_normalized.split()
    
    ref_word_count = len(ref_words)
    pred_word_count = len(pred_words)
    
    # Word Error Rate (WER)
    if ref_word_count == 0:
        wer = 0.0 if pred_word_count == 0 else 1.0
    else:
        # DP for word-level edit distance
        n, m = ref_word_count, pred_word_count
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = 0 if ref_words[i-1] == pred_words[j-1] else 1
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + cost  # substitution
                )
        
        word_edit_distance = dp[n][m]
        wer = word_edit_distance / ref_word_count
    
    wer_percentage = min(100.0, wer * 100)
    word_accuracy = max(0.0, 100.0 - wer_percentage)
    
    # Overall accuracy (weighted average favoring character accuracy)
    overall_accuracy = (character_accuracy * 0.6 + word_accuracy * 0.4)
    
    # Quality level assessment
    if overall_accuracy >= 95:
        quality_level = "Excellent"
    elif overall_accuracy >= 85:
        quality_level = "Very Good"
    elif overall_accuracy >= 75:
        quality_level = "Good"
    elif overall_accuracy >= 60:
        quality_level = "Fair"
    else:
        quality_level = "Poor"
    
    return {
        "overall_accuracy": round(overall_accuracy, 2),
        "wer": round(wer, 4),
        "wer_percentage": round(wer_percentage, 2),
        "character_accuracy": round(character_accuracy, 2),
        "word_accuracy": round(word_accuracy, 2),
        "quality_level": quality_level,
        "reference_word_count": ref_word_count,
        "predicted_word_count": pred_word_count
    }


@app.post("/api/evaluate-accuracy/", response_model=AccuracyResponse)
async def evaluate_accuracy(request: AccuracyRequest):
    """
    Evaluate accuracy between reference and predicted text.
    Supports both transcription and translation accuracy evaluation.
    """
    try:
        print(f"=== ACCURACY EVALUATION REQUEST ===")
        print(f"Mode: {request.mode}")
        print(f"Reference text (first 100): {request.reference_text[:100]}...")
        print(f"Predicted text (first 100): {request.predicted_text[:100]}...")
        print(f"===================================")
        
        metrics = calculate_accuracy_metrics(request.reference_text, request.predicted_text)
        
        print(f"Accuracy result: {metrics['overall_accuracy']}% ({metrics['quality_level']})")
        
        return AccuracyResponse(**metrics)
        
    except Exception as e:
        print(f"Error during accuracy evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Accuracy evaluation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)