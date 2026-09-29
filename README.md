# YouTube Video Extraction, Multilingual Transcription & Synchronized Text Highlighting System

An end-to-end full-stack platform built according to the system architecture diagram with **Next.js (React)** on the frontend, **Python FastAPI** on the backend, **MongoDB Atlas** for database storage, and an asynchronous pipeline powered by **yt-dlp**, **FFmpeg**, and **Whisper**.

---

## 🏗️ Architecture Overview

```
Frontend (Next.js / React)
  ├── YouTube URL Input
  ├── Video Player (Millisecond time sync & controls)
  ├── Transcript with Highlighting (Sentence & Word-level timestamps)
  ├── Language Selector (Telugu, Hindi, Spanish, French, etc.)
  ├── Search in Transcript (Keyword match & Jump to Timestamp)
  └── Download Center (MP4, MP3, TXT, SRT, VTT, Translated Subtitles)
          │
          │ HTTP / REST API (with JWT Auth)
          ▼
Backend (Python FastAPI)
  ├── /api/video/info         (Get Metadata)
  ├── /api/video/download     (Download Video)
  ├── /api/video/process      (Execute End-to-End Pipeline)
  ├── /api/audio/extract      (Extract Audio)
  ├── /api/transcription      (Speech to Text)
  ├── /api/translation        (Translate Text)
  ├── /api/transcript/{id}    (Get Transcript)
  ├── /api/download/{id}/*    (Download Files)
  └── /api/video/stream/{id}  (Stream Video)
          │
          ▼
Processing Pipeline (Asynchronous Workers)
  [1. yt-dlp] ➜ [2. FFmpeg Extraction] ➜ [3. Audio Preprocessing]
  ➜ [4. Whisper Speech-to-Text] ➜ [5. Text Processing (Word Timestamps)] ➜ [6. Translation]
          │
          ▼
Database (MongoDB Atlas)
  ├── videos Collection       ({ video_id, title, channel, duration, thumbnail, paths })
  ├── transcripts Collection  ({ video_id, language, segments: [{ start, end, text, words }] })
  └── translations Collection ({ video_id, source_language, target_language, segments })
```

---

## 🌟 Key Features

1. **YouTube Video & Audio Extraction**: Powered by `yt-dlp` and `FFmpeg` with high-efficiency multi-format extraction.
2. **Audio Preprocessing**: Automatically runs audio loudness normalization (`loudnorm`) and FFT noise reduction (`afftdn`) using `FFmpeg`.
3. **Speech to Text (STT)**: Automated speech recognition via YouTube timed text and OpenAI Whisper acoustic models.
4. **Word-Level Timestamps**: Every segment is tokenized with word-by-word start and end timing.
5. **Synchronized Text Highlighting**: Real-time highlighting of both the active sentence and the exact active word as the video plays.
6. **Search & Jump to Timestamp**: Instant in-transcript search with match counts and one-click jump seeking the video to that exact millisecond.
7. **Multilingual Translation**: Seamless AI translation into Telugu, Hindi, Spanish, French, German, Chinese, Japanese, Arabic, and more.
8. **Export & Download Center**: Direct export for:
   - Video (MP4)
   - Audio (MP3 / WAV)
   - Transcript (TXT)
   - Subtitles (SRT / WebVTT)
   - Translated Subtitles (SRT / TXT)
9. **MongoDB Atlas Ready**: Out-of-the-box support for MongoDB Atlas cloud clusters with resilient local JSON fallback.
10. **Interactive Pipeline Monitor**: Visual 6-stage tracker showing real-time worker progress and task completion.

---

## 🚀 Quick Start Guide

### 1. MongoDB Atlas Setup (Optional but Recommended)
Open `backend/.env` and paste your MongoDB Atlas cluster connection string:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/youtube_transcription?retryWrites=true&w=majority
MONGODB_DB_NAME=youtube_transcription
JWT_SECRET=super-secret-jwt-key-for-youtube-transcription-system-2026
```
*(If you do not have an Atlas URI ready, the system automatically uses a local persistent JSON database so you can test immediately without any extra setup!)*

---

### 2. Start the System

You can start both Backend and Frontend with a single click using:
```bash
# On Windows Command Prompt:
start.bat

# Or in PowerShell:
./start.ps1
```

Or run them individually in separate terminals:

#### Terminal 1: Backend (FastAPI)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Backend runs at: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

#### Terminal 2: Frontend (Next.js)
```bash
cd frontend
npm run dev
```
- Frontend UI runs at: `http://localhost:3000`

---

## 📂 Project Structure

```
youtube-transcription-system/
├── backend/
│   ├── app/
│   │   ├── config.py             # Paths, Atlas settings, Whisper config
│   │   ├── database.py           # MongoDB Atlas & local store manager
│   │   ├── models.py             # Pydantic data schemas
│   │   ├── main.py               # FastAPI app and static mounts
│   │   ├── pipeline/
│   │   │   ├── downloader.py      # Step 1: yt-dlp metadata & downloads
│   │   │   ├── audio_processor.py # Steps 2 & 3: FFmpeg extraction & filter
│   │   │   ├── transcriber.py     # Step 4: Whisper & Captions STT
│   │   │   ├── text_processor.py  # Step 5: Sentence split & word timestamps
│   │   │   ├── translator.py      # Step 6: Multi-language translation
│   │   │   └── storage.py         # Subtitle exporters (SRT, VTT, TXT)
│   │   └── routers/
│   │       ├── video.py           # Video info & full pipeline execution
│   │       ├── audio.py           # Audio extraction endpoints
│   │       ├── transcription.py   # Speech-to-text endpoints
│   │       ├── translation.py     # Multilingual translation endpoints
│   │       ├── download.py        # File export & download endpoints
│   │       ├── jobs.py            # Task queue progress tracking
│   │       └── auth.py            # JWT Authentication
│   ├── storage/                   # Local file storage (MP4, MP3, Subtitles)
│   └── .env                       # MongoDB Atlas & environment configuration
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Theme & layout
│   │   │   ├── page.tsx           # Main workspace application
│   │   │   └── globals.css        # Tailwind styling
│   │   ├── components/
│   │   │   ├── Header.tsx         # Nav, Atlas badge, quick sample selector
│   │   │   ├── VideoPlayer.tsx    # YouTube player with time tracking & seeking
│   │   │   ├── TranscriptViewer.tsx # Word/sentence highlight, search, jump
│   │   │   ├── DownloadSection.tsx# Export buttons for all file formats
│   │   │   ├── PipelineMonitor.tsx# 6-stage async pipeline status dialog
│   │   │   └── Icons.tsx          # Custom UI icons
│   │   ├── lib/
│   │   │   └── api.ts             # REST client for FastAPI endpoints
│   │   └── types/
│   │       └── index.ts           # TypeScript interfaces
├── start.bat                      # One-click Windows startup
├── start.ps1                      # PowerShell startup script
└── README.md
```
