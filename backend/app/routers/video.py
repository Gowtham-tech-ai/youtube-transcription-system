import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from app.config import VIDEOS_DIR, AUDIOS_DIR
from app.models import ProcessVideoRequest
from app.database import db_manager
from app.pipeline.downloader import extract_video_id, get_video_metadata, download_video_and_audio
from app.pipeline.audio_processor import extract_and_preprocess_audio
from app.pipeline.transcriber import get_transcription
from app.pipeline.translator import translate_segments
from app.pipeline.storage import save_subtitles

router = APIRouter(tags=["Video"])

class VideoInfoRequest(BaseModel):
    url: str

@router.post("/video/info")
async def get_info_endpoint(req: VideoInfoRequest):
    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or ID")
    
    # Check if already processed in database
    existing = await db_manager.get_video(video_id)
    if existing:
        return {"cached": True, "metadata": existing}
    
    metadata = get_video_metadata(req.url)
    return {"cached": False, "metadata": metadata}

async def run_pipeline_worker(job_id: str, video_id: str, target_url: str, target_languages: List[str], download_video_flag: bool):
    """
    Background Worker executing the entire pipeline shown in the architecture diagram:
    1. YouTube Downloader (yt-dlp)
    2. Audio Extraction (FFmpeg)
    3. Audio Preprocessing (Noise Reduction, Normalization)
    4. Speech to Text (Whisper / Captions)
    5. Text Processing (Sentence Split, Word Timestamps)
    6. Translation (Multi-language)
    And saving to MongoDB collections (videos, transcripts, translations).
    """
    try:
        # Step 1: Metadata & Video Download
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "processing",
            "stage": "downloading", "progress": 15, "message": "Extracting metadata and downloading audio/video streams..."
        })
        metadata = get_video_metadata(target_url)
        download_res = download_video_and_audio(video_id, download_video=download_video_flag)
        audio_path = download_res.get("audio_path")
        video_path = download_res.get("video_path")

        metadata["audio_path"] = audio_path
        metadata["video_path"] = video_path
        await db_manager.save_video(metadata)

        # Step 2 & 3: Audio Extraction & Preprocessing (FFmpeg)
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "processing",
            "stage": "preprocessing", "progress": 35, "message": "Pre-processing audio with FFmpeg (normalization, noise reduction)..."
        })
        clean_audio = None
        if audio_path:
            clean_audio = extract_and_preprocess_audio(audio_path, video_id)
            metadata["audio_path"] = clean_audio
            await db_manager.save_video(metadata)

        # Step 4 & 5: Speech to Text (Whisper) & Text Processing (Word timestamps)
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "processing",
            "stage": "transcribing", "progress": 60, "message": "Generating synchronized speech-to-text transcript & word timestamps..."
        })
        segments, detected_lang = get_transcription(video_id, clean_audio or audio_path)
        full_text = " ".join([s["text"] for s in segments if s.get("text")])

        transcript_doc = {
            "video_id": video_id,
            "language": detected_lang,
            "is_source": True,
            "full_text": full_text,
            "segments": segments
        }
        await db_manager.save_transcript(transcript_doc)
        save_subtitles(video_id, detected_lang, segments)

        # Step 6: Multi-language Translation
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "processing",
            "stage": "translating", "progress": 85, "message": "Translating transcript into selected target languages..."
        })
        
        for lang in (target_languages or ["te", "hi", "es"]):
            if lang != detected_lang:
                try:
                    trans_segments = translate_segments(segments, target_language=lang, source_language=detected_lang)
                    trans_full_text = " ".join([s["text"] for s in trans_segments if s.get("text")])
                    trans_doc = {
                        "video_id": video_id,
                        "source_language": detected_lang,
                        "target_language": lang,
                        "full_text": trans_full_text,
                        "segments": trans_segments
                    }
                    await db_manager.save_translation(trans_doc)
                    save_subtitles(video_id, lang, trans_segments)
                except Exception as te:
                    print(f"Failed translating to {lang}: {te}")

        # Completed
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "completed",
            "stage": "done", "progress": 100, "message": "Video processed, transcribed, and translated successfully!"
        })

    except Exception as e:
        await db_manager.update_job({
            "job_id": job_id, "video_id": video_id, "status": "failed",
            "stage": "error", "progress": 100, "message": f"Processing pipeline encountered an issue: {str(e)}",
            "error": str(e)
        })

@router.post("/video/process")
async def process_video_endpoint(req: ProcessVideoRequest, background_tasks: BackgroundTasks):
    video_id = extract_video_id(req.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job_record = {
        "job_id": job_id,
        "video_id": video_id,
        "status": "pending",
        "stage": "init",
        "progress": 5,
        "message": "Initializing asynchronous worker pipeline..."
    }
    await db_manager.update_job(job_record)

    # Launch background task
    background_tasks.add_task(
        run_pipeline_worker,
        job_id=job_id,
        video_id=video_id,
        target_url=req.url,
        target_languages=req.target_languages or ["te", "hi", "es"],
        download_video_flag=req.generate_video_file or False
    )

    return {
        "status": "accepted",
        "job_id": job_id,
        "video_id": video_id,
        "message": "Processing pipeline initiated successfully."
    }

@router.get("/video/{video_id}")
async def get_video_endpoint(video_id: str):
    video = await db_manager.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/video/stream/{video_id}")
async def stream_video(video_id: str):
    """
    Streams local video MP4 file with byte range support.
    """
    path = VIDEOS_DIR / f"{video_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video file not stored locally. Use YouTube embed player.")
    return FileResponse(str(path), media_type="video/mp4")

@router.get("/videos")
async def list_videos_endpoint(limit: int = 20):
    videos = await db_manager.list_videos(limit=limit)
    return {"videos": videos}

@router.get("/db/status")
async def get_db_status():
    return {
        "is_atlas_connected": db_manager.is_atlas_connected,
        "db_name": db_manager.db.name if db_manager.db is not None else "local_json_storage",
        "videos_count": len(await db_manager.list_videos(100)),
        "mode": "MongoDB Atlas (Cloud)" if db_manager.is_atlas_connected else "Local MongoDB/JSON Storage"
    }
