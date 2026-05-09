import base64
import os
import sys
import tempfile
import yt_dlp
from pathlib import Path
from config import TEMP_DIR

# nvm Node.js for local dev (bgutil uses Node.js; Docker already has it at /usr/bin)
_NVM_NODE = Path.home() / ".nvm/versions/node/v24.15.0/bin"
if _NVM_NODE.exists():
    os.environ["PATH"] = str(_NVM_NODE) + ":" + os.environ.get("PATH", "")

# Production: decode YOUTUBE_COOKIES_B64 env var into a temp file once at startup
_COOKIE_FILE: str | None = None

def _init_cookies() -> None:
    global _COOKIE_FILE
    b64 = os.environ.get("YOUTUBE_COOKIES_B64", "").strip()
    if not b64:
        return
    try:
        cookie_data = base64.b64decode(b64)
        tf = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", prefix="yt_cookies_", delete=False
        )
        tf.write(cookie_data)
        tf.flush()
        tf.close()
        _COOKIE_FILE = tf.name
    except Exception:
        pass

_init_cookies()


def _extractor_args() -> dict:
    # mweb: avoids SABR streaming restriction that blocks web client; bgutil plugin
    # auto-provides GVS PO Token for bot detection bypass.
    return {"youtube": {"player_client": ["mweb"]}}


def _proxy_opts() -> dict:
    # YOUTUBE_PROXY_URL: optional residential proxy to bypass datacenter IP blocks
    # e.g. "socks5://user:pass@host:port" or "http://user:pass@host:port"
    proxy = os.environ.get("YOUTUBE_PROXY_URL", "").strip()
    return {"proxy": proxy} if proxy else {}


def _auth_opts() -> dict:
    # Production: YOUTUBE_COOKIES_B64 env var
    if _COOKIE_FILE:
        return {"cookiefile": _COOKIE_FILE}
    # Local dev: cookies.txt next to repo root
    if sys.platform == "darwin":
        local_cookie = Path(__file__).resolve().parent.parent / "cookies.txt"
        if local_cookie.exists():
            return {"cookiefile": str(local_cookie)}
    return {}


def download_audio(job_id: str, url: str) -> str:
    """Download audio only (~30-60MB for 1h video). Returns audio file path."""
    output_dir = TEMP_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": str(output_dir / "audio.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
        "extractor_args": _extractor_args(),
        **_proxy_opts(),
        **_auth_opts(),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    audio_files = list(output_dir.glob("audio.*"))
    if not audio_files:
        raise RuntimeError("Audio download failed: no output file found")
    return str(audio_files[0])


def download_clip_segment(job_id: str, url: str, clip_idx: int, start: float, end: float) -> str:
    """Download only a specific time range of the video. Returns video file path."""
    output_dir = TEMP_DIR / job_id / f"clip_{clip_idx}"
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(output_dir / "raw.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "download_ranges": lambda info, __: [{"start_time": start, "end_time": end}],
        "force_keyframes_at_cuts": True,
        "js_runtimes": {"node": {}},
        "remote_components": {"ejs:github"},
        "extractor_args": _extractor_args(),
        **_proxy_opts(),
        **_auth_opts(),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    raw_files = list(output_dir.glob("raw.*"))
    if not raw_files:
        raise RuntimeError(f"Segment download failed for clip {clip_idx}")
    return str(raw_files[0])
