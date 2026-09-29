from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.pipeline.downloader import download_video_and_audio
from app.pipeline.audio_processor import extract_and_preprocess_audio
from app.database import db_manager

router = APIRouter(prefix="/audio", tags=["Audio"])

class AudioExtractRequest(BaseModel):
    video_id: str

@router.post("/extract")
async def extract_audio_endpoint(req: AudioExtractRequest):
    video_id = req.video_id
    video = await db_manager.get_video(video_id)
    
    # Download audio if not existing
    download_res = download_video_and_audio(video_id, download_video=False)
    raw_audio = download_res.get("audio_path")
    if not raw_audio:
        raise HTTPException(status_code=400, detail="Could not extract audio for this video")

    # Step 3: FFmpeg audio preprocessing (loudness norm + noise reduction)
    clean_audio = extract_and_preprocess_audio(raw_audio, video_id)

    if video:
        video["audio_path"] = clean_audio
        await db_manager.save_video(video)

    return {
        "status": "success",
        "video_id": video_id,
        "audio_path": clean_audio,
        "message": "Audio extracted and preprocessed successfully with FFmpeg"
    }
