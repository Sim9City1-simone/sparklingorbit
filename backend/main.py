import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional

from database import engine, init_db
from models import Job, Clip
from jobs import process_job, get_job_clips, _transcript_path, _segments_path, _video_path
from config import TEMP_DIR
from services.editor import DEFAULT_STYLE


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
        job = Job(youtube_url=req.url)
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
        job_id = clip.job_id
        clip_idx = clip.clip_idx

    segments_path = _segments_path(job_id)
    if not segments_path.exists():
        raise HTTPException(status_code=404, detail="Segments data not found")

    segments = json.loads(segments_path.read_text(encoding="utf-8"))
    if clip_idx >= len(segments):
        raise HTTPException(status_code=404, detail="Clip index out of range")

    video = _video_path(job_id)
    if not video:
        raise HTTPException(status_code=404, detail="Original video not found")

    from services.editor import render_clip
    fmt = req.fmt
    style = req.style or DEFAULT_STYLE
    suffix = f"_{fmt.replace(':', 'x')}"

    file_path = await asyncio.to_thread(
        render_clip, job_id, clip_idx, str(video), segments[clip_idx],
        fmt=fmt, style=style, suffix=suffix,
    )

    # Build public URL relative to TEMP_DIR
    relative = Path(file_path).relative_to(TEMP_DIR)
    return {"url": f"/clips/{relative}"}


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


@app.get("/health")
def health():
    return {"status": "ok"}
