from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    words: Optional[List[WordTimestamp]] = []

class VideoMetadata(BaseModel):
    video_id: str
    url: str
    title: str
    channel: Optional[str] = "Unknown"
    duration: float = 0.0
    thumbnail: Optional[str] = ""
    view_count: Optional[int] = 0
    description: Optional[str] = ""
    video_path: Optional[str] = None
    audio_path: Optional[str] = None
    source_language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VideoDocument(VideoMetadata):
    id: Optional[str] = None

class TranscriptDocument(BaseModel):
    id: Optional[str] = None
    video_id: str
    language: str = "en"
    is_source: bool = True
    full_text: str = ""
    segments: List[TranscriptSegment] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TranslationDocument(BaseModel):
    id: Optional[str] = None
    video_id: str
    source_language: str = "en"
    target_language: str
    segments: List[TranscriptSegment] = []
    full_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class JobStatus(BaseModel):
    job_id: str
    video_id: str
    status: str  # pending, processing, completed, failed
    stage: str  # init, downloading, extracting_audio, preprocessing, transcribing, text_processing, translating, done
    progress: int = 0  # 0 to 100
    message: str = ""
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    name: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TranslationRequest(BaseModel):
    video_id: str
    target_language: str
    source_language: Optional[str] = "en"

class ProcessVideoRequest(BaseModel):
    url: str
    target_languages: Optional[List[str]] = ["es", "hi", "te", "fr"]
    generate_video_file: Optional[bool] = False
