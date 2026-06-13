import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import httpx
import requests
from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_settings, update_settings

router = APIRouter()

SENSITIVE_KEYS = ("gemini_api_key", "openai_api_key", "elevenlabs_api_key")


def _mask(value: str) -> str:
    if not value:
        return ""
    return "•••••" + value[-4:]


def _public_settings(settings) -> dict:
    return {
        "script_provider": settings.script_provider,
        "ollama_model": settings.ollama_model,
        "ollama_url": settings.ollama_url,
        "gemini_api_key": _mask(settings.gemini_api_key),
        "openai_api_key": _mask(settings.openai_api_key),
        "voice_provider": settings.voice_provider,
        "elevenlabs_api_key": _mask(settings.elevenlabs_api_key),
        "image_provider": settings.image_provider,
        "local_sd_url": settings.local_sd_url,
    }


@router.get("")
def read_settings():
    return _public_settings(get_settings())


class SettingsUpdate(BaseModel):
    script_provider: str | None = None
    ollama_model: str | None = None
    ollama_url: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    voice_provider: str | None = None
    elevenlabs_api_key: str | None = None
    image_provider: str | None = None
    local_sd_url: str | None = None


@router.post("")
def write_settings(body: SettingsUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    # Do not overwrite a stored key with its masked representation.
    for key in SENSITIVE_KEYS:
        if key in fields and fields[key].startswith("•••••"):
            fields.pop(key)
    update_settings(fields)
    return {"success": True}


# ---------------------------------------------------------------------------
# Connectivity tests
# ---------------------------------------------------------------------------

def _test_ollama(s) -> tuple[bool, str]:
    try:
        r = httpx.get(f"{s.ollama_url}/api/tags", timeout=5)
        r.raise_for_status()
        return True, f"Connected to Ollama at {s.ollama_url}"
    except Exception as e:
        return False, f"Ollama not reachable at {s.ollama_url}: {e}"


def _test_local_sd(s) -> tuple[bool, str]:
    try:
        r = httpx.get(f"{s.local_sd_url}/sdapi/v1/sd-models", timeout=5)
        r.raise_for_status()
        return True, f"Connected to AUTOMATIC1111 at {s.local_sd_url}"
    except Exception as e:
        return False, f"Stable Diffusion not reachable at {s.local_sd_url}: {e}"


def _test_kokoro(s) -> tuple[bool, str]:
    try:
        from kokoro import KPipeline  # noqa: F401
        KPipeline(lang_code="a")
        return True, "Kokoro TTS available"
    except Exception as e:
        return False, f"Kokoro not available: {e}"


def _test_ffmpeg(s) -> tuple[bool, str]:
    if shutil.which("ffmpeg") is None:
        return False, "ffmpeg not found on PATH"
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True
        )
        first = result.stdout.splitlines()[0] if result.stdout else "ffmpeg"
        return True, first
    except Exception as e:
        return False, f"ffmpeg error: {e}"


def _test_gemini(s) -> tuple[bool, str]:
    if not s.gemini_api_key:
        return False, "Gemini API key not set"
    try:
        import google.generativeai as genai

        genai.configure(api_key=s.gemini_api_key)
        list(genai.list_models())
        return True, "Gemini API key valid"
    except Exception as e:
        return False, f"Gemini error: {e}"


def _test_openai(s) -> tuple[bool, str]:
    if not s.openai_api_key:
        return False, "OpenAI API key not set"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=s.openai_api_key)
        client.models.list()
        return True, "OpenAI API key valid"
    except Exception as e:
        return False, f"OpenAI error: {e}"


def _test_elevenlabs(s) -> tuple[bool, str]:
    if not s.elevenlabs_api_key:
        return False, "ElevenLabs API key not set"
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": s.elevenlabs_api_key},
            timeout=10,
        )
        r.raise_for_status()
        return True, "ElevenLabs API key valid"
    except Exception as e:
        return False, f"ElevenLabs error: {e}"


_TESTS = {
    "ollama": _test_ollama,
    "local_sd": _test_local_sd,
    "kokoro": _test_kokoro,
    "gemini": _test_gemini,
    "openai": _test_openai,
    "elevenlabs": _test_elevenlabs,
}


class TestRequest(BaseModel):
    service: str


@router.post("/test")
def test_service(body: TestRequest):
    s = get_settings()
    fn = _TESTS.get(body.service)
    if fn is None:
        return {"success": False, "message": f"Unknown service: {body.service}"}
    ok, message = fn(s)
    return {"success": ok, "message": message}


@router.get("/status")
def status():
    s = get_settings()

    def run(fn):
        try:
            ok, detail = fn(s)
        except Exception as e:  # pragma: no cover - defensive
            ok, detail = False, str(e)
        return ok, detail

    checks = {
        "ollama": _test_ollama,
        "local_sd": _test_local_sd,
        "kokoro": _test_kokoro,
        "ffmpeg": _test_ffmpeg,
        "gemini": _test_gemini,
        "openai": _test_openai,
        "elevenlabs": _test_elevenlabs,
    }

    with ThreadPoolExecutor(max_workers=len(checks)) as ex:
        results = dict(zip(checks.keys(), ex.map(run, checks.values())))

    out = {}
    for name, (ok, detail) in results.items():
        if name == "ffmpeg":
            out[name] = {"ok": ok, "version": detail}
        else:
            out[name] = {"ok": ok, "detail": detail}
    return out
