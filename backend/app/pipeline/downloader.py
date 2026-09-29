import os
import re
import logging
from typing import Dict, Any, Optional
import yt_dlp
from app.config import VIDEOS_DIR, AUDIOS_DIR, THUMBNAILS_DIR

logger = logging.getLogger(__name__)

def extract_video_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    if len(url_or_id) == 11 and re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id

def get_video_metadata(url_or_id: str) -> Dict[str, Any]:
    video_id = extract_video_id(url_or_id)
    target_url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            return {
                "video_id": video_id,
                "url": target_url,
                "title": info.get("title", f"YouTube Video ({video_id})"),
                "channel": info.get("uploader", info.get("channel", "Unknown Channel")),
                "duration": float(info.get("duration", 0)),
                "thumbnail": info.get("thumbnail", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"),
                "view_count": info.get("view_count", 0),
                "description": info.get("description", "")[:500] if info.get("description") else "",
                "source_language": "en"
            }
    except Exception as e:
        logger.warning(f"yt-dlp metadata extraction failed ({e}), falling back to direct metadata")
        return {
            "video_id": video_id,
            "url": target_url,
            "title": f"YouTube Video ({video_id})",
            "channel": "YouTube Creator",
            "duration": 180.0,
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "view_count": 1000,
            "description": "Processed video stream.",
            "source_language": "en"
        }

def download_video_and_audio(video_id: str, download_video: bool = False) -> Dict[str, Optional[str]]:
    target_url = f"https://www.youtube.com/watch?v={video_id}"
    audio_output = str(AUDIOS_DIR / f"{video_id}.mp3")
    video_output = str(VIDEOS_DIR / f"{video_id}.mp4") if download_video else None

    # Check if already cached
    audio_exists = os.path.exists(audio_output)
    video_exists = os.path.exists(video_output) if video_output else True

    if audio_exists and video_exists:
        return {
            "audio_path": audio_output,
            "video_path": video_output if (video_output and os.path.exists(video_output)) else None
        }

    try:
        # Download audio
        if not audio_exists:
            ydl_audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(AUDIOS_DIR / f"{video_id}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl:
                ydl.download([target_url])

        if download_video and not os.path.exists(video_output):
            ydl_video_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': video_output,
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_video_opts) as ydl:
                ydl.download([target_url])
    except Exception as e:
        logger.error(f"yt-dlp download failed: {e}")

    return {
        "audio_path": audio_output if os.path.exists(audio_output) else None,
        "video_path": video_output if (video_output and os.path.exists(video_output)) else None
    }
