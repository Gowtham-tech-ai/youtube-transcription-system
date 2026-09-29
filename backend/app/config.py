import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
VIDEOS_DIR = STORAGE_DIR / "videos"
AUDIOS_DIR = STORAGE_DIR / "audios"
SUBTITLES_DIR = STORAGE_DIR / "subtitles"
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"

for d in [STORAGE_DIR, VIDEOS_DIR, AUDIOS_DIR, SUBTITLES_DIR, THUMBNAILS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "YouTube Transcription & Multilingual Translation System"
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb+srv://admin:admin@cluster0.mongodb.net/youtube_transcription?retryWrites=true&w=majority")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "youtube_transcription")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-for-youtube-transcription-system-2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "tiny")
    DEFAULT_LANGUAGE: str = "en"

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "allow"

settings = Settings()
