from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATABASE_URL
from app.models import AppSettings

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db():
    """Create all tables and ensure the singleton AppSettings row exists."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = session.get(AppSettings, "singleton")
        if existing is None:
            session.add(AppSettings(id="singleton"))
            session.commit()


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_settings() -> AppSettings:
    """Return the singleton AppSettings row, creating it if missing."""
    with Session(engine) as session:
        settings = session.get(AppSettings, "singleton")
        if settings is None:
            settings = AppSettings(id="singleton")
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return settings


def update_settings(fields: dict) -> AppSettings:
    """Partial update of the singleton AppSettings row."""
    from datetime import datetime

    allowed = set(AppSettings.model_fields.keys())
    with Session(engine) as session:
        settings = session.get(AppSettings, "singleton")
        if settings is None:
            settings = AppSettings(id="singleton")
            session.add(settings)
        for key, value in fields.items():
            if key in allowed and key not in ("id", "updated_at"):
                setattr(settings, key, value)
        settings.updated_at = datetime.utcnow()
        session.add(settings)
        session.commit()
        session.refresh(settings)
        return settings
