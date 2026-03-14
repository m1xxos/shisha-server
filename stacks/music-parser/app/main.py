"""FastAPI application for Music Parser."""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from downloader import DownloadRequest, download_and_process

app = FastAPI(title="Music Parser")

# Thread pool for blocking I/O (yt-dlp / ffmpeg)
_executor = ThreadPoolExecutor(max_workers=4)

# In-memory job store  {job_id: {"status": ..., "message": ..., "file": ...}}
_jobs: dict[str, dict] = {}


# ── Request / response schemas ────────────────────────────────────────────────

class DownloadPayload(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    @field_validator("url")
    @classmethod
    def url_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()


# ── API routes ────────────────────────────────────────────────────────────────

@app.post("/api/download", status_code=202)
async def create_download(payload: DownloadPayload, background_tasks: BackgroundTasks):
    """Queue a download job and return its ID immediately."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "message": "Queued"}
    background_tasks.add_task(_run_download, job_id, payload)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll the status of a download job."""
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ── Background task ───────────────────────────────────────────────────────────

async def _run_download(job_id: str, payload: DownloadPayload) -> None:
    _jobs[job_id] = {"status": "downloading", "message": "Downloading audio…"}
    loop = asyncio.get_event_loop()
    try:
        req = DownloadRequest(
            url=payload.url,
            start_time=payload.start_time,
            end_time=payload.end_time,
            title=payload.title,
            artist=payload.artist,
            album=payload.album,
        )
        filename = await loop.run_in_executor(_executor, download_and_process, req)
        _jobs[job_id] = {
            "status": "done",
            "message": f"Saved: {filename}",
            "file": filename,
        }
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id] = {"status": "error", "message": str(exc)}


# ── Static files (must be last) ───────────────────────────────────────────────

_STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
