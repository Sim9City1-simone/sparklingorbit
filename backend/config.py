import os
from pathlib import Path

TEMP_DIR = Path(os.getenv("TEMP_DIR", "/data/clips"))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("DB_PATH", "/data/sparkling.db")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
MAX_CLIP_DURATION = int(os.getenv("MAX_CLIP_DURATION", "90"))
MIN_CLIP_DURATION = int(os.getenv("MIN_CLIP_DURATION", "30"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "")
