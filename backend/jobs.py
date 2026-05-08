import asyncio
import json
from pathlib import Path
from sqlmodel import Session, select
from database import engine
from models import Job, Clip
from config import TEMP_DIR
from datetime import datetime
import traceback


def update_job_status(job_id: str, status: str, error: str = None):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if job:
            job.status = status
            job.error = error
            job.updated_at = datetime.utcnow()
            session.add(job)
            session.commit()


def save_clips(job_id: str, clips: list[dict]):
    with Session(engine) as session:
        for idx, clip in enumerate(clips):
            db_clip = Clip(
                job_id=job_id,
                clip_idx=idx,
                start_time=clip["start"],
                end_time=clip["end"],
                score=clip["score"],
                title=clip["title"],
                reason=clip.get("reason", ""),
                file_path=clip["file_path"],
            )
            session.add(db_clip)
        session.commit()


def get_job_clips(job_id: str) -> list[dict]:
    with Session(engine) as session:
        clips = session.exec(select(Clip).where(Clip.job_id == job_id)).all()
        return [c.model_dump() for c in clips]


def _transcript_path(job_id: str) -> Path:
    return TEMP_DIR / job_id / "transcript.json"


def _segments_path(job_id: str) -> Path:
    return TEMP_DIR / job_id / "segments.json"


def _video_path(job_id: str) -> Path | None:
    job_dir = TEMP_DIR / job_id
    for f in job_dir.glob("video.*"):
        return f
    return None


async def process_job(job_id: str, youtube_url: str):
    from services.downloader import download_audio
    from services.transcriber import transcribe, transcribe_from_url
    from services.scorer import score_segments
    from services.editor import edit_clips_from_url

    try:
        # Phase 1+2: fetch YouTube captions (no download) → fallback to audio + Whisper
        update_job_status(job_id, "transcribing")
        transcript = await asyncio.to_thread(transcribe_from_url, youtube_url)

        if transcript is None:
            update_job_status(job_id, "downloading")
            audio_path = await asyncio.to_thread(download_audio, job_id, youtube_url)
            update_job_status(job_id, "transcribing")
            transcript = await asyncio.to_thread(transcribe, audio_path)
            Path(audio_path).unlink(missing_ok=True)

        _transcript_path(job_id).write_text(
            json.dumps(transcript, ensure_ascii=False), encoding="utf-8"
        )

        # Phase 3: score → find the 5 best segments
        update_job_status(job_id, "scoring")
        segments = score_segments(transcript)

        _segments_path(job_id).write_text(
            json.dumps(segments, ensure_ascii=False), encoding="utf-8"
        )

        # Phase 4: download + render only the selected clip segments, delete raw after each
        update_job_status(job_id, "editing")
        clips = await asyncio.to_thread(edit_clips_from_url, job_id, youtube_url, segments)

        save_clips(job_id, clips)
        update_job_status(job_id, "done")

    except Exception:
        update_job_status(job_id, "error", error=traceback.format_exc())
