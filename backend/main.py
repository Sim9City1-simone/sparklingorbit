import asyncio
import json
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional

from database import engine, init_db
from models import Job, Clip, Creator, SocialAccount
from jobs import process_job, get_job_clips, _transcript_path, _segments_path
from config import TEMP_DIR
from services.editor import DEFAULT_STYLE, render_clip
from services.downloader import download_clip_segment


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SparklingOrbit API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/clips", StaticFiles(directory=str(TEMP_DIR)), name="clips")


class ProcessRequest(BaseModel):
    url: str
    creator_id: Optional[str] = None


class ShareRequest(BaseModel):
    clip_id: str
    platform: str  # youtube | tiktok | instagram
    title: str
    description: str = ""


class ReexportRequest(BaseModel):
    clip_id: str
    fmt: str = "9:16"       # 9:16 | 1:1 | 16:9
    style: Optional[dict] = None


@app.post("/process")
async def start_process(req: ProcessRequest, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        job = Job(youtube_url=req.url, creator_id=req.creator_id)
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

    background_tasks.add_task(process_job, job_id, req.url)
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        clips = get_job_clips(job_id)
        return {
            "id": job.id,
            "status": job.status,
            "error": job.error,
            "created_at": job.created_at,
            "clips": clips,
        }


@app.get("/jobs/{job_id}/transcript")
def get_transcript(job_id: str):
    path = _transcript_path(job_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Transcript not ready yet")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "text": data.get("text", ""),
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"]}
            for s in data.get("segments", [])
        ],
    }


@app.post("/reexport")
async def reexport_clip(req: ReexportRequest):
    """Re-render a clip with a different format or caption style."""
    with Session(engine) as session:
        clip = session.get(Clip, req.clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        job = session.get(Job, clip.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job_id = clip.job_id
        clip_idx = clip.clip_idx
        youtube_url = job.youtube_url
        start_time = clip.start_time
        end_time = clip.end_time

    segments_path = _segments_path(job_id)
    if not segments_path.exists():
        raise HTTPException(status_code=404, detail="Segments data not found")

    segments = json.loads(segments_path.read_text(encoding="utf-8"))
    if clip_idx >= len(segments):
        raise HTTPException(status_code=404, detail="Clip index out of range")

    fmt = req.fmt
    style = req.style or DEFAULT_STYLE
    suffix = f"_{fmt.replace(':', 'x')}_re"

    def _do_reexport() -> str:
        raw_path = download_clip_segment(job_id, youtube_url, clip_idx, start_time, end_time)
        try:
            seg = segments[clip_idx]
            offset = seg["start"]
            local_seg = {
                **seg,
                "start": 0.0,
                "end": seg["end"] - offset,
                "segments": [
                    {
                        **s,
                        "start": s["start"] - offset,
                        "end": s["end"] - offset,
                        "words": [
                            {**w, "start": w["start"] - offset, "end": w["end"] - offset}
                            for w in s.get("words", [])
                        ],
                    }
                    for s in seg["segments"]
                ],
            }
            return render_clip(job_id, clip_idx, raw_path, local_seg, fmt=fmt, style=style, suffix=suffix)
        finally:
            Path(raw_path).unlink(missing_ok=True)

    file_path = await asyncio.to_thread(_do_reexport)
    relative = Path(file_path).relative_to(TEMP_DIR)
    ts = int(time.time())
    return {"url": f"/clips/{relative}?t={ts}"}


@app.post("/share")
async def share_clip(req: ShareRequest):
    with Session(engine) as session:
        clip = session.get(Clip, req.clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        if req.platform == "youtube":
            from services.social.youtube import upload_to_youtube
            result = await asyncio.to_thread(
                upload_to_youtube, clip.file_path, req.title, req.description
            )
        elif req.platform == "tiktok":
            from services.social.tiktok import upload_to_tiktok
            result = await asyncio.to_thread(upload_to_tiktok, clip.file_path, req.title)
        elif req.platform == "instagram":
            from services.social.instagram import upload_to_instagram
            result = await asyncio.to_thread(
                upload_to_instagram, clip.file_path, req.title
            )
        else:
            raise HTTPException(status_code=400, detail="Platform not supported")

        return result


# ─── Creator endpoints ────────────────────────────────────────────────────────

class CreatorCreate(BaseModel):
    name: str
    avatar_url: Optional[str] = None


class SocialAccountUpsert(BaseModel):
    platform: str  # youtube | tiktok | instagram
    access_token: str = ""
    refresh_token: str = ""
    platform_user_id: str = ""
    username: str = ""


@app.get("/creators")
def list_creators():
    with Session(engine) as session:
        creators = session.exec(select(Creator).order_by(Creator.created_at)).all()
        result = []
        for c in creators:
            accounts = session.exec(
                select(SocialAccount).where(SocialAccount.creator_id == c.id)
            ).all()
            result.append({
                **c.model_dump(),
                "social_accounts": [a.model_dump() for a in accounts],
            })
        return result


@app.post("/creators", status_code=201)
def create_creator(req: CreatorCreate):
    with Session(engine) as session:
        creator = Creator(name=req.name, avatar_url=req.avatar_url)
        session.add(creator)
        session.commit()
        session.refresh(creator)
        return creator.model_dump()


@app.delete("/creators/{creator_id}", status_code=204)
def delete_creator(creator_id: str):
    with Session(engine) as session:
        creator = session.get(Creator, creator_id)
        if not creator:
            raise HTTPException(status_code=404, detail="Creator not found")
        session.exec(select(SocialAccount).where(SocialAccount.creator_id == creator_id))
        for acc in session.exec(select(SocialAccount).where(SocialAccount.creator_id == creator_id)).all():
            session.delete(acc)
        session.delete(creator)
        session.commit()


@app.put("/creators/{creator_id}/social/{platform}")
def upsert_social_account(creator_id: str, platform: str, req: SocialAccountUpsert):
    with Session(engine) as session:
        creator = session.get(Creator, creator_id)
        if not creator:
            raise HTTPException(status_code=404, detail="Creator not found")
        existing = session.exec(
            select(SocialAccount).where(
                SocialAccount.creator_id == creator_id,
                SocialAccount.platform == platform,
            )
        ).first()
        if existing:
            existing.access_token = req.access_token
            existing.refresh_token = req.refresh_token
            existing.platform_user_id = req.platform_user_id
            existing.username = req.username
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing.model_dump()
        account = SocialAccount(
            creator_id=creator_id,
            platform=platform,
            access_token=req.access_token,
            refresh_token=req.refresh_token,
            platform_user_id=req.platform_user_id,
            username=req.username,
        )
        session.add(account)
        session.commit()
        session.refresh(account)
        return account.model_dump()


@app.delete("/creators/{creator_id}/social/{platform}", status_code=204)
def disconnect_social(creator_id: str, platform: str):
    with Session(engine) as session:
        account = session.exec(
            select(SocialAccount).where(
                SocialAccount.creator_id == creator_id,
                SocialAccount.platform == platform,
            )
        ).first()
        if account:
            session.delete(account)
            session.commit()


# ─── Jobs history ─────────────────────────────────────────────────────────────

@app.get("/jobs")
def list_jobs():
    with Session(engine) as session:
        jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
        result = []
        for job in jobs:
            creator = session.get(Creator, job.creator_id) if job.creator_id else None
            clips_count = len(session.exec(select(Clip).where(Clip.job_id == job.id)).all())
            result.append({
                **job.model_dump(),
                "creator_name": creator.name if creator else None,
                "creator_avatar": creator.avatar_url if creator else None,
                "clips_count": clips_count,
            })
        return result


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        for clip in session.exec(select(Clip).where(Clip.job_id == job_id)).all():
            session.delete(clip)
        session.delete(job)
        session.commit()
    job_dir = TEMP_DIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
