import subprocess
from pathlib import Path

from app.models import AppSettings, Series

KOKORO_VOICES = [
    {"voice_id": "af_heart",    "name": "Emma — American Female, Warm",         "provider": "kokoro"},
    {"voice_id": "af_bella",    "name": "Bella — American Female, Clear",       "provider": "kokoro"},
    {"voice_id": "af_nicole",   "name": "Nicole — American Female, Soft",       "provider": "kokoro"},
    {"voice_id": "af_sarah",    "name": "Sarah — American Female, Bright",      "provider": "kokoro"},
    {"voice_id": "am_adam",     "name": "Adam — American Male, Deep",           "provider": "kokoro"},
    {"voice_id": "am_michael",  "name": "Michael — American Male, Neutral",     "provider": "kokoro"},
    {"voice_id": "bf_emma",     "name": "Sophie — British Female, Warm",        "provider": "kokoro"},
    {"voice_id": "bf_isabella", "name": "Isabella — British Female, Clear",     "provider": "kokoro"},
    {"voice_id": "bm_george",   "name": "George — British Male, Authoritative", "provider": "kokoro"},
    {"voice_id": "bm_lewis",    "name": "Lewis — British Male, Narrative",      "provider": "kokoro"},
]

_KOKORO_IDS = {v["voice_id"] for v in KOKORO_VOICES}


def generate_voiceovers(
    scenes: list,
    series: Series,
    settings: AppSettings,
    workspace_dir: Path,
    log_fn,
) -> list:
    """Returns list of audio file Paths in scene order. Sets scene.actual_duration."""
    if settings.voice_provider == "kokoro" or series.voice_id in _KOKORO_IDS:
        paths = _generate_kokoro(scenes, series.voice_id, workspace_dir, log_fn)
    else:
        paths = _generate_elevenlabs(
            scenes, series.voice_id, settings.elevenlabs_api_key, workspace_dir, log_fn
        )

    for scene in scenes:
        if not scene.actual_duration:
            scene.actual_duration = float(scene.duration_hint)
    return paths


def _generate_kokoro(scenes, voice_id, workspace_dir, log_fn):
    from kokoro import KPipeline
    import numpy as np
    import soundfile as sf

    lang = "b" if voice_id.startswith("b") else "a"
    pipeline = KPipeline(lang_code=lang)

    if voice_id not in _KOKORO_IDS:
        voice_id = "af_heart"

    paths = []
    for scene in scenes:
        out_path = workspace_dir / f"scene_{scene.scene_number}_audio.wav"
        all_audio = []
        try:
            generator = pipeline(scene.narration, voice=voice_id, speed=0.95)
            for _, _, audio in generator:
                all_audio.append(audio)
        except Exception:
            # Fall back to default voice if the chosen voice fails to load.
            generator = pipeline(scene.narration, voice="af_heart", speed=0.95)
            all_audio = []
            for _, _, audio in generator:
                all_audio.append(audio)

        combined = np.concatenate(all_audio) if len(all_audio) > 1 else all_audio[0]
        sf.write(str(out_path), combined, 24000)
        scene.actual_duration = len(combined) / 24000.0
        paths.append(out_path)
        log_fn("info", f"Generated voice for scene {scene.scene_number} ({scene.actual_duration:.1f}s)")
    return paths


def _generate_elevenlabs(scenes, voice_id, api_key, workspace_dir, log_fn):
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    client = ElevenLabs(api_key=api_key)
    paths = []
    for scene in scenes:
        out_path = workspace_dir / f"scene_{scene.scene_number}_audio.mp3"
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=scene.narration,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        )
        with open(out_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(out_path)],
            capture_output=True, text=True,
        )
        try:
            scene.actual_duration = float(result.stdout.strip())
        except ValueError:
            scene.actual_duration = 0.0
        paths.append(out_path)
        log_fn("info", f"Generated voice for scene {scene.scene_number}")
    return paths
