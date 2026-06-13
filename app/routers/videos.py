import asyncio
import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session, select

from app.database import engine
from app.models import GenerationLog, Series, Video, VideoStatus

router = APIRouter()


@router.get("")
def list_videos(
    series_id: Optional[str] = None,
    limit: int = Query(20),
    offset: int = Query(0),
):
    with Session(engine) as session:
        stmt = select(Video)
        if series_id:
            stmt = stmt.where(Video.series_id == series_id)
        stmt = stmt.order_by(Video.created_at.desc()).offset(offset).limit(limit)
        return session.exec(stmt).all()


@router.get("/{video_id}")
def get_video(video_id: str):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if not video:
            raise HTTPException(404, "Video not found")
        data = video.model_dump()
        if video.script_json:
            try:
                data["script_json"] = json.loads(video.script_json)
            except Exception:
                pass
        return data


@router.get("/{video_id}/download")
def download_video(video_id: str):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if not video or video.status != VideoStatus.COMPLETE or not video.output_path:
            raise HTTPException(404, "Video not complete")
        if not os.path.exists(video.output_path):
            raise HTTPException(404, "Video file not found")
        filename = os.path.basename(video.output_path)
        return FileResponse(video.output_path, media_type="video/mp4", filename=filename)


@router.get("/{video_id}/logs")
def get_logs(video_id: str):
    with Session(engine) as session:
        logs = session.exec(
            select(GenerationLog)
            .where(GenerationLog.video_id == video_id)
            .order_by(GenerationLog.timestamp)
        ).all()
        return logs


@router.delete("/{video_id}")
def delete_video(video_id: str):
    with Session(engine) as session:
        video = session.get(Video, video_id)
        if not video:
            raise HTTPException(404, "Video not found")
        output_path = video.output_path
        logs = session.exec(
            select(GenerationLog).where(GenerationLog.video_id == video_id)
        ).all()
        for entry in logs:
            session.delete(entry)
        session.delete(video)
        session.commit()
    if output_path and os.path.exists(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass
    return {"success": True}


async def event_stream(video_id: str):
    last_log_id = 0
    while True:
        with Session(engine) as session:
            new_logs = session.exec(
                select(GenerationLog)
                .where(GenerationLog.video_id == video_id)
                .where(GenerationLog.id > last_log_id)
                .order_by(GenerationLog.id)
            ).all()

            for entry in new_logs:
                payload = {
                    "id": entry.id,
                    "level": entry.level,
                    "message": entry.message,
                    "progress_pct": entry.progress_pct,
                    "timestamp": entry.timestamp.isoformat(),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                last_log_id = entry.id

            video = session.get(Video, video_id)
            if video and video.status in (VideoStatus.COMPLETE, VideoStatus.FAILED):
                yield f"data: {json.dumps({'level': 'done', 'status': video.status.value})}\n\n"
                break

        await asyncio.sleep(1)


@router.get("/{video_id}/stream")
async def stream_logs(video_id: str):
    return StreamingResponse(
        event_stream(video_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
