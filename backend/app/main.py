import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, STORAGE_DIR, VIDEOS_DIR, AUDIOS_DIR, SUBTITLES_DIR, THUMBNAILS_DIR
from app.database import db_manager
from app.routers import video, audio, transcription, translation, download, auth, jobs

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing YouTube Transcription & Multilingual Translation Backend...")
    # Initialize MongoDB Atlas connection
    await db_manager.connect()
    yield
    if db_manager.client:
        db_manager.client.close()
        logger.info("Closed MongoDB connections.")

app = FastAPI(
    title=settings.APP_NAME,
    description="High-performance backend for YouTube Video Extraction, Multilingual Transcription & Synchronized Text Highlighting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for direct download/playback
app.mount("/storage/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")
app.mount("/storage/audios", StaticFiles(directory=str(AUDIOS_DIR)), name="audios")
app.mount("/storage/subtitles", StaticFiles(directory=str(SUBTITLES_DIR)), name="subtitles")
app.mount("/storage/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="thumbnails")

# Include Routers
app.include_router(video.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(transcription.router, prefix="/api")
app.include_router(translation.router, prefix="/api")
app.include_router(download.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs_url": "/docs",
        "mongodb_atlas_connected": db_manager.is_atlas_connected
    }
