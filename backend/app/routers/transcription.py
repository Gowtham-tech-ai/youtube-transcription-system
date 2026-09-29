from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.pipeline.transcriber import get_transcription
from app.pipeline.storage import save_subtitles
from app.database import db_manager

router = APIRouter(tags=["Transcription"])

class TranscribeRequest(BaseModel):
    video_id: str
    force_whisper: Optional[bool] = False

@router.post("/transcription")
async def transcribe_endpoint(req: TranscribeRequest):
    video_id = req.video_id
    video = await db_manager.get_video(video_id)
    audio_path = video.get("audio_path") if video else None

    # Step 4 & 5: Speech to text & text processing
    segments, detected_lang = get_transcription(video_id, audio_path)
    full_text = " ".join([s["text"] for s in segments if s.get("text")])

    # Save to database
    transcript_doc = {
        "video_id": video_id,
        "language": detected_lang,
        "is_source": True,
        "full_text": full_text,
        "segments": segments
    }
    await db_manager.save_transcript(transcript_doc)

    # Save Subtitle files (SRT, VTT, TXT)
    save_subtitles(video_id, detected_lang, segments)

    return {
        "status": "success",
        "video_id": video_id,
        "language": detected_lang,
        "segment_count": len(segments),
        "transcript": transcript_doc
    }

@router.get("/transcript/{video_id}")
async def get_transcript_endpoint(video_id: str, lang: str = "en"):
    transcript = await db_manager.get_transcript(video_id, lang)
    if not transcript:
        # Check if there is any language transcript for this video
        fallback = await db_manager.get_transcript(video_id, "en")
        if fallback:
            return fallback
        raise HTTPException(status_code=404, detail="Transcript not found for this video")
    return transcript
