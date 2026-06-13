import json
import threading
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.config import OUTPUTS_DIR, WORKSPACE_DIR
from app.database import engine, get_settings
from app.models import GenerationLog, Series, Video, VideoStatus
from app.services.image_service import generate_images
from app.services.script_service import generate_script
from app.services.video_service import assemble_video
from app.services.voice_service import generate_voiceovers

scheduler = BackgroundScheduler()
RUNNING_JOBS: dict = {}  # series_id -> {video_id, started_at}
JOBS_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def log(video_id: str, level: str, message: str, progress_pct: int = None, session=None):
    """Insert a GenerationLog row. Creates its own DB session if none provided."""
    entry = GenerationLog(
        video_id=video_id, level=level, message=message, progress_pct=progress_pct
    )
    if session is not None:
        session.add(entry)
        session.commit()
        return
    with Session(engine) as s:
        s.add(entry)
        s.commit()


def _create_video_row(series_id: str, triggered_by: str = "scheduler") -> str:
    with Session(engine) as session:
        video = Video(
            series_id=series_id,
            status=VideoStatus.PENDING,
            triggered_by=triggered_by,
        )
        session.add(video)
        session.commit()
        session.refresh(video)
        return video.id


def update_video_status(video_id: str, status: VideoStatus):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if video:
            video.status = status
            session.add(video)
            session.commit()


def update_video_complete(video_id, output_path, duration, scene_count, script_json):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if video:
            video.status = VideoStatus.COMPLETE
            video.output_path = output_path
            video.duration_seconds = duration
            video.scene_count = scene_count
            video.script_json = script_json
            video.completed_at = datetime.utcnow()
            session.add(video)
            session.commit()


def update_video_failed(video_id: str, error_message: str):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if video:
            video.status = VideoStatus.FAILED
            video.error_message = error_message
            video.completed_at = datetime.utcnow()
            session.add(video)
            session.commit()


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def start_scheduler():
    scheduler.start()
    _load_all_series_jobs()


def shutdown_scheduler():
    scheduler.shutdown(wait=False)


def _load_all_series_jobs():
    with Session(engine) as session:
        series_list = session.exec(select(Series).where(Series.is_active == True)).all()  # noqa: E712
    for series in series_list:
        try:
            schedule_series(series)
        except Exception:
            pass


def schedule_series(series: Series):
    """Add or replace the APScheduler job for this series."""
    job_id = f"series_{series.id}"
    hour, minute = series.schedule_time.split(":")
    tz = pytz.timezone(series.schedule_timezone)
    post_time = datetime.now(tz).replace(
        hour=int(hour), minute=int(minute), second=0, microsecond=0
    )
    gen_time = post_time - timedelta(hours=6)
    scheduler.add_job(
        run_generation_job,
        trigger=CronTrigger(
            hour=gen_time.hour, minute=gen_time.minute, timezone=series.schedule_timezone
        ),
        args=[series.id],
        id=job_id,
        replace_existing=True,
    )


def unschedule_series(series_id: str):
    job_id = f"series_{series_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_generation_job(series_id: str):
    """Full pipeline entry point used by the scheduler. Runs in a background thread."""
    with JOBS_LOCK:
        if series_id in RUNNING_JOBS:
            return  # Already running

    video_id = _create_video_row(series_id, triggered_by="scheduler")

    with JOBS_LOCK:
        RUNNING_JOBS[series_id] = {
            "video_id": video_id,
            "started_at": datetime.utcnow().isoformat(),
        }

    try:
        _run_pipeline(series_id, video_id)
    finally:
        with JOBS_LOCK:
            RUNNING_JOBS.pop(series_id, None)


def _run_pipeline(series_id: str, video_id: str):
    with Session(engine) as session:
        series = session.get(Series, series_id)
    settings = get_settings()

    workspace_dir = WORKSPACE_DIR / video_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    def log_fn(level, message, progress_pct=None):
        log(video_id, level, message, progress_pct)

    try:
        update_video_status(video_id, VideoStatus.GENERATING_SCRIPT)
        log_fn("info", f"Starting generation for series '{series.name}'", 0)
        log_fn("info", "Requesting script from AI...", 5)

        script = generate_script(series, settings)
        log_fn("success", f"Script written: '{script.title}' — {len(script.scenes)} scenes", 15)

        update_video_status(video_id, VideoStatus.GENERATING_AUDIO)
        audio_paths = generate_voiceovers(script.scenes, series, settings, workspace_dir, log_fn)
        log_fn("success", "All voiceovers generated", 35)

        update_video_status(video_id, VideoStatus.GENERATING_IMAGES)
        image_paths = generate_images(script.scenes, series, settings, workspace_dir, log_fn)
        log_fn("success", "All images generated", 70)

        update_video_status(video_id, VideoStatus.ASSEMBLING)
        log_fn("info", "Assembling video...", 71)
        output_path = OUTPUTS_DIR / series_id / f"{video_id}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = assemble_video(
            script.scenes, audio_paths, image_paths, series, output_path, workspace_dir, log_fn
        )

        update_video_complete(
            video_id, str(output_path), duration, len(script.scenes), json.dumps(asdict(script))
        )
        log_fn("success", f"Video ready: {output_path.name}", 100)

    except Exception as e:
        log_fn("error", f"Generation failed: {str(e)}")
        update_video_failed(video_id, str(e))
        raise
