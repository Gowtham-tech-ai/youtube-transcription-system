Write-Host "=========================================================================" -ForegroundColor Cyan
Write-Host "YouTube Video Extraction, Multilingual Transcription & Highlighting System" -ForegroundColor Cyan
Write-Host "=========================================================================" -ForegroundColor Cyan

# Check if MongoDB URI is in backend/.env
Write-Host "Checking configuration..." -ForegroundColor Yellow

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot/backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot/frontend'; npm.cmd run dev"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "Backend Docs: http://localhost:8000/docs" -ForegroundColor White
