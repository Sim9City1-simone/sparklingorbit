from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid


class Creator(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SocialAccount(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    creator_id: str = Field(foreign_key="creator.id")
    platform: str  # youtube | tiktok | instagram
    access_token: str = ""
    refresh_token: str = ""
    platform_user_id: str = ""
    username: str = ""
    connected_at: datetime = Field(default_factory=datetime.utcnow)


class Job(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    youtube_url: str
    creator_id: Optional[str] = Field(default=None, foreign_key="creator.id")
    status: str = "pending"
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Clip(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job.id")
    clip_idx: int = 0
    start_time: float
    end_time: float
    score: float
    title: str
    reason: str = ""
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
