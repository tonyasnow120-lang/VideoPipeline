import requests
from fastapi import APIRouter

from app.database import get_settings
from app.services.voice_service import KOKORO_VOICES

router = APIRouter()


@router.get("")
def list_voices():
    voices = [dict(v) for v in KOKORO_VOICES]

    settings = get_settings()
    if settings.elevenlabs_api_key:
        try:
            r = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": settings.elevenlabs_api_key},
                timeout=10,
            )
            r.raise_for_status()
            for v in r.json().get("voices", []):
                voices.append({
                    "voice_id": v.get("voice_id"),
                    "name": v.get("name"),
                    "provider": "elevenlabs",
                    "preview_url": v.get("preview_url"),
                })
        except Exception:
            # On failure, return Kokoro voices only (no error).
            pass

    return voices
