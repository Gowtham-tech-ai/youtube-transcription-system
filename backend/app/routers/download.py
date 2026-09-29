import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from app.config import VIDEOS_DIR, AUDIOS_DIR, SUBTITLES_DIR
from app.database import db_manager
from app.pipeline.storage import generate_srt, generate_vtt, generate_txt

router = APIRouter(prefix="/download", tags=["Download"])

@router.get("/{video_id}/{file_type}")
async def download_file(video_id: str, file_type: str, lang: str = "en"):
    """
    Download video (mp4), audio (mp3/wav), subtitles (srt/vtt), or transcript (txt).
    """
    file_type = file_type.lower()

    if file_type == "mp4" or file_type == "video":
        path = VIDEOS_DIR / f"{video_id}.mp4"
        if not path.exists():
            # Check if there is any mp4 matching
            raise HTTPException(status_code=404, detail="Video MP4 file not yet downloaded or available locally")
        return FileResponse(str(path), media_type="video/mp4", filename=f"{video_id}.mp4")

    elif file_type == "mp3" or file_type == "audio":
        path = AUDIOS_DIR / f"{video_id}.mp3"
        clean_wav = AUDIOS_DIR / f"{video_id}_clean.wav"
        if path.exists():
            return FileResponse(str(path), media_type="audio/mpeg", filename=f"{video_id}.mp3")
        elif clean_wav.exists():
            return FileResponse(str(clean_wav), media_type="audio/wav", filename=f"{video_id}.wav")
        raise HTTPException(status_code=404, detail="Audio file not yet extracted")

    elif file_type in ["srt", "vtt", "txt"]:
        # First check subtitle file on disk
        sub_file = SUBTITLES_DIR / f"{video_id}_{lang}.{file_type}"
        if sub_file.exists():
            media = "text/plain" if file_type == "txt" else "application/x-subrip" if file_type == "srt" else "text/vtt"
            return FileResponse(str(sub_file), media_type=media, filename=f"{video_id}_{lang}.{file_type}")

        # Otherwise build on-the-fly from database
        data = None
        if lang == "en":
            data = await db_manager.get_transcript(video_id, "en")
        else:
            data = await db_manager.get_translation(video_id, lang)

        if not data or not data.get("segments"):
            raise HTTPException(status_code=404, detail=f"Transcript or translation in '{lang}' not available")

        segments = data["segments"]
        if file_type == "srt":
            content = generate_srt(segments)
            return PlainTextResponse(content, media_type="application/x-subrip", headers={"Content-Disposition": f'attachment; filename="{video_id}_{lang}.srt"'})
        elif file_type == "vtt":
            content = generate_vtt(segments)
            return PlainTextResponse(content, media_type="text/vtt", headers={"Content-Disposition": f'attachment; filename="{video_id}_{lang}.vtt"'})
        else:
            content = generate_txt(segments)
            return PlainTextResponse(content, media_type="text/plain", headers={"Content-Disposition": f'attachment; filename="{video_id}_{lang}.txt"'})

    raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_type}")
