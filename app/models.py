from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class AppSettings(SQLModel, table=True):
    id: str = Field(default="singleton", primary_key=True)
    # Script generation
    script_provider: str = Field(default="ollama")  # "ollama" | "gemini" | "openai"
    ollama_model: str = Field(default="llama3.3:8b")
    ollama_url: str = Field(default="http://localhost:11434")
    gemini_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    # Voice generation
    voice_provider: str = Field(default="kokoro")  # "kokoro" | "elevenlabs"
    elevenlabs_api_key: str = Field(default="")
    # Image generation
    image_provider: str = Field(default="local_sd")  # "local_sd" | "openai_images"
    local_sd_url: str = Field(default="http://localhost:7860")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Series(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    niche: str
    custom_niche: Optional[str] = Field(default=None)
    art_style: str
    voice_id: str
    voice_name: str
    caption_style: str
    music_track: Optional[str] = Field(default=None)
    music_volume: float = Field(default=0.10)
    schedule_time: str = Field(default="09:00")
    schedule_timezone: str = Field(default="UTC")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoStatus(str, Enum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_IMAGES = "generating_images"
    ASSEMBLING = "assembling"
    COMPLETE = "complete"
    FAILED = "failed"


class Video(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    series_id: str = Field(foreign_key="series.id")
    status: VideoStatus = Field(default=VideoStatus.PENDING)
    script_json: Optional[str] = Field(default=None)
    output_path: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    scene_count: Optional[int] = Field(default=None)
    triggered_by: str = Field(default="scheduler")  # "scheduler" | "manual"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)


class GenerationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: str = Field(foreign_key="video.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str  # "info" | "success" | "error" | "progress"
    message: str
    progress_pct: Optional[int] = Field(default=None)  # 0-100
