from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models import TranslationRequest
from app.pipeline.translator import translate_segments, SUPPORTED_LANGUAGES
from app.pipeline.storage import save_subtitles
from app.database import db_manager

router = APIRouter(prefix="/translation", tags=["Translation"])

@router.get("/languages")
async def get_supported_languages():
    return {"languages": SUPPORTED_LANGUAGES}

@router.post("")
async def translate_endpoint(req: TranslationRequest):
    video_id = req.video_id
    target_lang = req.target_language.lower()
    source_lang = (req.source_language or "en").lower()

    # Check if translation already exists
    existing = await db_manager.get_translation(video_id, target_lang)
    if existing:
        return {"status": "cached", "translation": existing}

    # Fetch original transcript
    base_transcript = await db_manager.get_transcript(video_id, source_lang)
    if not base_transcript:
        # Check source video language
        base_transcript = await db_manager.get_transcript(video_id, "en")
    
    if not base_transcript or not base_transcript.get("segments"):
        raise HTTPException(status_code=400, detail="Base transcript not found. Run transcription first.")

    # Translate segments
    translated_segments = translate_segments(
        segments=base_transcript["segments"],
        target_language=target_lang,
        source_language=source_lang
    )

    full_text = " ".join([s["text"] for s in translated_segments if s.get("text")])

    translation_doc = {
        "video_id": video_id,
        "source_language": source_lang,
        "target_language": target_lang,
        "full_text": full_text,
        "segments": translated_segments
    }

    # Save to MongoDB
    await db_manager.save_translation(translation_doc)

    # Save Subtitle files for translated language
    save_subtitles(video_id, target_lang, translated_segments)

    return {
        "status": "success",
        "video_id": video_id,
        "target_language": target_lang,
        "translation": translation_doc
    }

@router.get("/{video_id}/{target_language}")
async def get_translation_endpoint(video_id: str, target_language: str):
    trans = await db_manager.get_translation(video_id, target_language.lower())
    if not trans:
        raise HTTPException(status_code=404, detail="Translation not found for this language")
    return trans
