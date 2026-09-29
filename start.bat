@echo off
echo =========================================================================
echo YouTube Video Extraction, Multilingual Transcription & Highlighting System
echo =========================================================================

echo Starting FastAPI Backend on http://localhost:8000 ...
start "Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Next.js Frontend on http://localhost:3000 ...
start "Frontend (Next.js)" cmd /k "cd frontend && npm.cmd run dev"

echo.
echo System successfully launched!
echo Open your browser at: http://localhost:3000
echo Backend API Docs at: http://localhost:8000/docs
echo =========================================================================
pause
