from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import engine
from app.models import Series, Video
from app.scheduler import schedule_series, unschedule_series

router = APIRouter()


class SeriesCreate(BaseModel):
    name: str
    niche: str
    custom_niche: Optional[str] = None
    art_style: str
    voice_id: str
    voice_name: str
    caption_style: str
    music_track: Optional[str] = None
    music_volume: float = 0.10
    schedule_time: str = "09:00"
    schedule_timezone: str = "UTC"
    is_active: bool = True


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    niche: Optional[str] = None
    custom_niche: Optional[str] = None
    art_style: Optional[str] = None
    voice_id: Optional[str] = None
    voice_name: Optional[str] = None
    caption_style: Optional[str] = None
    music_track: Optional[str] = None
    music_volume: Optional[float] = None
    schedule_time: Optional[str] = None
    schedule_timezone: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
def list_series():
    with Session(engine) as session:
        rows = session.exec(select(Series).order_by(Series.created_at.desc())).all()
        return rows


@router.post("")
def create_series(body: SeriesCreate):
    with Session(engine) as session:
        series = Series(**body.model_dump())
        session.add(series)
        session.commit()
        session.refresh(series)
        result = series
    if result.is_active:
        try:
            schedule_series(result)
        except Exception:
            pass
    return result


@router.get("/{series_id}")
def get_series(series_id: str):
    with Session(engine) as session:
        series = session.get(Series, series_id)
        if not series:
            raise HTTPException(404, "Series not found")
        return series


@router.put("/{series_id}")
def update_series(series_id: str, body: SeriesUpdate):
    with Session(engine) as session:
        series = session.get(Series, series_id)
        if not series:
            raise HTTPException(404, "Series not found")
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(series, key, value)
        session.add(series)
        session.commit()
        session.refresh(series)
        result = series

    # Reschedule based on the updated state.
    try:
        unschedule_series(series_id)
        if result.is_active:
            schedule_series(result)
    except Exception:
        pass
    return result


@router.delete("/{series_id}")
def delete_series(series_id: str):
    with Session(engine) as session:
        series = session.get(Series, series_id)
        if not series:
            raise HTTPException(404, "Series not found")
        videos = session.exec(select(Video).where(Video.series_id == series_id)).all()
        for v in videos:
            session.delete(v)
        session.delete(series)
        session.commit()
    try:
        unschedule_series(series_id)
    except Exception:
        pass
    return {"success": True}


@router.patch("/{series_id}/toggle")
def toggle_series(series_id: str):
    with Session(engine) as session:
        series = session.get(Series, series_id)
        if not series:
            raise HTTPException(404, "Series not found")
        series.is_active = not series.is_active
        session.add(series)
        session.commit()
        session.refresh(series)
        result = series

    try:
        if result.is_active:
            schedule_series(result)
        else:
            unschedule_series(series_id)
    except Exception:
        pass
    return {"is_active": result.is_active}
