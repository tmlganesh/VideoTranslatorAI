# Video Transcription Pipeline

A complete full-stack application for video transcription using FastAPI backend and React frontend. This application can transcribe audio from video URLs (YouTube, etc.) using AI-powered speech recognition.

## Features

- **Video URL Input**: Support for various video platforms (YouTube, etc.)
- **AI Transcription**: Uses OpenAI's Whisper model for accurate speech-to-text
- **Modern UI**: Clean, responsive React interface
- **Real-time Progress**: Loading indicators and error handling
- **Copy to Clipboard**: Easy text copying functionality

## Project Structure

```
videoTranslation/
├── backend/
│   ├── main.py           # FastAPI server with transcription endpoint
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   ├── App.css      # Styling
│   │   ├── main.jsx     # React entry point
│   │   └── index.css    # Global styles
│   ├── index.html       # HTML template
│   ├── package.json     # Node.js dependencies
│   └── vite.config.js   # Vite configuration
└── README.md            # This file
```

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **Node.js 16+** - [Download Node.js](https://nodejs.org/)
3. **FFmpeg** - Required for audio processing
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (CentOS/RHEL)

## Installation & Setup

### Step 1: Clone or Setup Project

If you haven't already, navigate to your project directory:
```powershell
cd c:\Users\thega\Downloads\videoTranslation
```

### Step 2: Backend Setup (FastAPI)

1. **Navigate to backend directory:**
   ```powershell
   cd backend
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Python dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Start the FastAPI server:**
   ```powershell
   python main.py
   ```

   The backend API will be available at: `http://localhost:8000`
   
   You can verify it's working by visiting: `http://localhost:8000/docs` (FastAPI auto-generated documentation)

### Step 3: Frontend Setup (React)

Open a **new terminal/command prompt** and:

1. **Navigate to frontend directory:**
   ```powershell
   cd c:\Users\thega\Downloads\videoTranslation\frontend
   ```

2. **Install Node.js dependencies:**
   ```powershell
   npm install
   ```

3. **Start the React development server:**
   ```powershell
   npm run dev
   ```

   The frontend will be available at: `http://localhost:5173`

## Usage

1. **Start both servers** (backend and frontend) as described above
2. **Open your browser** and go to `http://localhost:5173`
3. **Enter a video URL** (e.g., YouTube link) in the input field
4. **Click "Transcribe Video"** and wait for processing
5. **View the transcription** result and copy it if needed

## API Endpoints

### Backend API (FastAPI - Port 8000)

- **GET /** - Health check endpoint
- **POST /api/transcribe/** - Transcribe video from URL
  - Body: `{"video_url": "https://youtube.com/watch?v=..."}`
  - Response: `{"transcription": "...", "status": "success"}`

## Troubleshooting

### Common Issues

1. **FFmpeg not found error:**
   - Ensure FFmpeg is installed and added to system PATH
   - Restart terminal after installation

2. **CORS errors:**
   - Make sure backend is running on port 8000
   - Check that frontend is accessing `http://localhost:8000`

3. **Port conflicts:**
   - Backend default: 8000 (change in `main.py`)
   - Frontend default: 5173 (change in `vite.config.js`)

4. **Python virtual environment issues:**
   - On Windows, you might need to enable script execution: 
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
     ```

5. **Video download failures:**
   - Some videos may be restricted or require authentication
   - Try with different video URLs (YouTube public videos work best)

### Performance Notes

- First transcription may take longer as Whisper downloads the model
- Processing time depends on video length
- Whisper "base" model is used for balance of speed/accuracy

## Development

### Backend Development

- FastAPI with automatic OpenAPI documentation
- CORS enabled for frontend communication
- Temporary file cleanup for audio processing
- Error handling and validation

### Frontend Development

- React with Vite for fast development
- Modern CSS with gradients and animations
- Responsive design for mobile devices
- Loading states and error handling

### Extending the Application

**Add more transcription options:**
- Different Whisper model sizes (`tiny`, `small`, `medium`, `large`)
- Language detection and specific language transcription
- Timestamp information in transcriptions

**Improve UI/UX:**
- File upload support for local videos
- Progress bars for transcription
- History of previous transcriptions

**Add features:**
- User authentication
- Save transcriptions to database
- Export to different formats (SRT, VTT, etc.)

## Dependencies

### Backend (Python)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `yt-dlp` - Video/audio downloader
- `openai-whisper` - AI transcription model
- `pydantic` - Data validation

### Frontend (Node.js)
- `react` - UI framework  
- `vite` - Build tool and dev server
- Standard React development tools

## License

This project is for educational/personal use. Please respect video content copyrights and platform terms of service when using this tool.