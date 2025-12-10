from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import whisper
import os
import tempfile
import uvicorn
import shutil
import glob
import re
import requests
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')

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
print("Loading Whisper Large model for reliable performance...")
model = whisper.load_model("large")  # Most stable model
print("Whisper Large model loaded successfully!")

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

def get_youtube_transcript(video_id, target_languages=['te', 'hi', 'en', 'auto']):
    """
    Try to fetch YouTube transcript using YouTube Transcript API.
    Prioritizes Telugu, then Hindi, then English for better regional language support.
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
        
        # Try to find transcript in preferred languages (Telugu prioritized)
        transcript = None
        selected_lang = None
        
        # First, try to find manually created transcripts
        for lang in target_languages:
            try:
                if lang == 'auto':
                    # Try to get the first available manually created transcript
                    for t in transcript_list:
                        if not t.is_generated:
                            transcript = t.fetch()
                            selected_lang = t.language_code
                            break
                else:
                    transcript = transcript_list.find_transcript([lang]).fetch()
                    selected_lang = lang
                    break
            except:
                continue
        
        # If no manual transcript found, try auto-generated
        if not transcript:
            try:
                # Get auto-generated transcript (usually in the video's original language)
                for t in transcript_list:
                    if t.is_generated:
                        transcript = t.fetch()
                        selected_lang = t.language_code
                        break
            except:
                pass
        
        if transcript:
            # Format transcript text
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(transcript)
            
            # Clean up the transcript text
            transcript_text = transcript_text.replace('\n', ' ').strip()
            
            # Get language name
            detected_language_name = language_names.get(selected_lang, selected_lang.upper())
            
            print(f"YouTube transcript found: {detected_language_name} ({selected_lang})")
            print(f"Transcript length: {len(transcript_text)} characters")
            
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

async def translate_with_sarvam_ai(text: str, source_language: str, target_language: str):
    """
    Translate text using Sarvam AI API with high accuracy for Indian languages.
    Handles long texts by splitting into chunks under 2000 characters.
    """
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=500, detail="Sarvam AI API key not configured")
    
    # Language code mapping for Sarvam AI
    sarvam_language_map = {
        'en': 'en-IN',
        'hi': 'hi-IN', 
        'te': 'te-IN',
        'ta': 'ta-IN',
        'kn': 'kn-IN',
        'ml': 'ml-IN',
        'gu': 'gu-IN',
        'mr': 'mr-IN',
        'bn': 'bn-IN',
        'or': 'or-IN',
        'pa': 'pa-IN',
        'as': 'as-IN'
    }
    
    # Map to Sarvam AI language codes
    source_lang = sarvam_language_map.get(source_language, 'en-IN')
    target_lang = sarvam_language_map.get(target_language, 'te-IN')
    
    print(f"=== SARVAM AI TRANSLATION DEBUG ===")
    print(f"Input source_language: '{source_language}'")
    print(f"Input target_language: '{target_language}'")
    print(f"Mapped source_lang: '{source_lang}'")
    print(f"Mapped target_lang: '{target_lang}'")
    print(f"Text length: {len(text)} characters")
    print(f"API Key present: {bool(SARVAM_API_KEY)}")
    print(f"===================================")
    
    # Split text into chunks if it's longer than 1800 characters (leaving some buffer)
    max_chunk_size = 1800
    text_chunks = []
    
    if len(text) <= max_chunk_size:
        text_chunks = [text]
    else:
        # Split by sentences first to maintain context
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') <= max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    text_chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            text_chunks.append(current_chunk.strip())
    
    print(f"Translating {len(text_chunks)} chunk(s) of text...")
    
    translated_chunks = []
    
    try:
        url = 'https://api.sarvam.ai/translate'
        headers = {
            'api-subscription-key': SARVAM_API_KEY,
            'content-type': 'application/json'
        }
        
        for i, chunk in enumerate(text_chunks):
            print(f"Translating chunk {i+1}/{len(text_chunks)} ({len(chunk)} chars)...")
            
            payload = {
                "input": chunk,
                "source_language_code": source_lang,
                "target_language_code": target_lang,
                "model": "sarvam-translate:v1",
                "mode": "formal",
                "numerals_format": "native",
                "speaker_gender": "Male",
                "enable_preprocessing": True
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"API Response Status: {response.status_code}")
            print(f"API Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('translated_text', chunk)
                print(f"Translated text preview: {translated_text[:100]}...")
                translated_chunks.append(translated_text)
            else:
                print(f"Sarvam AI translation error for chunk {i+1}: {response.status_code} - {response.text}")
                # Use original chunk if translation fails
                translated_chunks.append(chunk)
        
        # Join all translated chunks
        final_translation = ' '.join(translated_chunks)
        return final_translation
        
    except requests.exceptions.RequestException as e:
        print(f"Sarvam AI API request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation request failed: {str(e)}")
    except Exception as e:
        print(f"Sarvam AI translation error: {str(e)}")
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
    target_language: str = None  # Optional translation target language

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
        print(f"Target Language Type: {type(request.target_language)}")
        print(f"===================================")
        
        # Check if it's a YouTube URL and try to get existing transcript first
        video_id = extract_youtube_video_id(request.video_url)
        
        if video_id:
            print(f"YouTube video detected (ID: {video_id}). Trying to fetch existing transcript...")
            transcript_text, lang_code, lang_name = get_youtube_transcript(video_id)
            
            if transcript_text:
                print("Successfully retrieved YouTube transcript! Skipping audio processing.")
                
                # Handle translation if requested
                translation_text = None
                target_lang = None
                print(f"=== TRANSLATION ATTEMPT DEBUG ===")
                print(f"Request target language: '{request.target_language}'")
                print(f"Condition check: {request.target_language and request.target_language != 'Same as Original (No Translation)'}")
                print(f"=================================")
                
                if request.target_language and request.target_language != "Same as Original (No Translation)":
                    try:
                        print(f"Starting translation from {lang_code} to {request.target_language}")
                        print(f"Transcript text (first 200 chars): {transcript_text[:200]}...")
                        translation_text = await translate_with_sarvam_ai(
                            text=transcript_text,
                            source_language=lang_code,
                            target_language=request.target_language
                        )
                        print(f"Translation result (first 200 chars): {translation_text[:200]}...")
                        target_lang = request.target_language
                        print(f"Translation completed for YouTube transcript")
                    except Exception as e:
                        print(f"Translation failed for YouTube transcript: {str(e)}")
                        # Continue without translation rather than failing
                
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
            
            # Instead of trying to detect language, let's directly transcribe with auto-detection
            result = model.transcribe(audio_file_path, language=None)
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
            
            print(f"Direct transcription successful. Language: {detected_language_code}")
            
        except Exception as lang_detect_error:
            print(f"Language detection failed: {lang_detect_error}")
            print("Falling back to direct transcription without language detection...")
            
            # Fallback: direct transcription
            result = model.transcribe(audio_file_path)
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
        
        # Get language name
        language_names = {
            'en': 'English', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'kn': 'Kannada',
            'ml': 'Malayalam', 'bn': 'Bengali', 'gu': 'Gujarati', 'mr': 'Marathi', 'pa': 'Punjabi',
            'ur': 'Urdu', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
            'fr': 'French', 'de': 'German', 'es': 'Spanish', 'pt': 'Portuguese', 'ru': 'Russian',
            'it': 'Italian', 'tr': 'Turkish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian'
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
        if request.target_language and request.target_language != "Same as Original (No Translation)":
            try:
                translation_text = await translate_with_sarvam_ai(
                    text=transcription_text,
                    source_language=detected_language_code,
                    target_language=request.target_language
                )
                target_lang = request.target_language
                print(f"Translation completed for video transcription")
            except Exception as e:
                print(f"Translation failed for video transcription: {str(e)}")
                # Continue without translation rather than failing
        
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

@app.post("/api/transcribe-file/", response_model=TranscriptionResponse)
async def transcribe_uploaded_file(file: UploadFile = File(...)):
    """
    Transcribe audio from an uploaded file using whisper with language detection.
    """
    try:
        # Create a temporary file for the uploaded file
        with tempfile.NamedTemporaryFile(suffix=f".{file.filename.split('.')[-1]}", delete=False) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
        
        print("Loading audio for language detection...")
        
        try:
            # Load audio and detect language
            audio = whisper.load_audio(temp_file_path)
            print(f"Audio loaded, shape: {audio.shape if hasattr(audio, 'shape') else 'unknown'}")
            
            audio = whisper.pad_or_trim(audio)
            print(f"Audio after padding/trimming, shape: {audio.shape if hasattr(audio, 'shape') else 'unknown'}")
            
            # Instead of trying to detect language, let's directly transcribe with auto-detection
            result = model.transcribe(temp_file_path, language=None)
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
            
            print(f"Direct transcription successful. Language: {detected_language_code}")
            
        except Exception as lang_detect_error:
            print(f"Language detection failed: {lang_detect_error}")
            print("Falling back to direct transcription without language detection...")
            
            # Fallback: direct transcription
            result = model.transcribe(temp_file_path)
            detected_language_code = result.get('language', 'en')
            transcription_text = result["text"].strip()
        
        # Get language name
        language_names = {
            'en': 'English', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'kn': 'Kannada',
            'ml': 'Malayalam', 'bn': 'Bengali', 'gu': 'Gujarati', 'mr': 'Marathi', 'pa': 'Punjabi',
            'ur': 'Urdu', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
            'fr': 'French', 'de': 'German', 'es': 'Spanish', 'pt': 'Portuguese', 'ru': 'Russian',
            'it': 'Italian', 'tr': 'Turkish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian'
        }
        
        detected_language_name = language_names.get(detected_language_code, detected_language_code.upper())
        
        print(f"Detected language: {detected_language_name} ({detected_language_code})")
        
        # Apply language-specific improvements
        transcription_text = improve_telugu_transcription(transcription_text, detected_language_code)
        
        print(f"File transcription completed: {transcription_text[:100]}...")
        
        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except OSError:
            pass
        
        return TranscriptionResponse(
            transcription=transcription_text,
            detected_language=detected_language_name,
            language_code=detected_language_code,
            status="success_file_transcription",
            translation="",
            target_language=""
        )
    
    except Exception as e:
        print(f"Error during file transcription: {str(e)}")
        
        # Clean up temporary file in case of error
        try:
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except OSError:
            pass
        
        raise HTTPException(status_code=500, detail=f"File transcription failed: {str(e)}")

@app.post("/api/translate/", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text using Sarvam AI with high accuracy for Indian languages.
    Supports multiple Indian languages including Telugu, Hindi, Tamil, etc.
    """
    try:
        print(f"Translation request: {request.source_language} -> {request.target_language}")
        print(f"Text to translate: {request.text[:100]}...")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to translate cannot be empty")
        
        # Use Sarvam AI for translation
        translated_text = await translate_with_sarvam_ai(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language
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
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        print(f"Error during translation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)