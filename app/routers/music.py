from fastapi import APIRouter

from app.config import MUSIC_DIR

router = APIRouter()


@router.get("")
def list_music():
    out = []
    for path in sorted(MUSIC_DIR.glob("*.mp3")):
        display = path.stem.replace("_", " ").title()
        out.append({"filename": path.name, "display_name": display})
    return out
