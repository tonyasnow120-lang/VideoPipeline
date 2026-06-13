import json
from dataclasses import dataclass, field

from app.config import ART_STYLE_DESCRIPTORS
from app.models import AppSettings, Series


@dataclass
class SceneScript:
    scene_number: int
    narration: str
    image_prompt: str
    duration_hint: int
    actual_duration: float = 0.0


@dataclass
class GeneratedScript:
    title: str
    topic: str
    scenes: list = field(default_factory=list)


SYSTEM_PROMPT_TEMPLATE = """You are a short-form video scriptwriter specializing in faceless viral content.
You write scripts for {niche} videos that are engaging, dramatic, and optimized for
TikTok, Instagram Reels, and YouTube Shorts.

Rules:
- Total video: 45-90 seconds of spoken content
- Number of scenes: 5-8
- Each narration: 15-25 words (spoken at ~2.5 words/second)
- Style: punchy, present tense, hook-driven, no filler
- Scene 1 narration MUST open with a strong hook - curiosity or mild shock
- No camera directions or stage directions in narration
- Each image_prompt must be detailed and visual, written for a Stable Diffusion model

Return ONLY valid JSON. No markdown fences, no preamble. Schema:
{{
  "title": "string",
  "topic": "string",
  "scenes": [
    {{ "scene_number": 1, "narration": "string", "image_prompt": "string" }}
  ]
}}"""

USER_PROMPT_TEMPLATE = """Create a {niche} video script. Visual style: {art_style_descriptor}.
{custom_line}Pick a specific, compelling topic. Avoid generic subjects.

Each image_prompt must:
- Describe a single cinematic scene
- Open with: "{art_style_descriptor}"
- Be self-contained (no assumed prior frames)
- Be 2-4 sentences of visual description
- Contain NO text, words, logos, or UI elements in the scene"""


def _build_prompts(series: Series) -> tuple[str, str]:
    niche = series.niche
    art_style_descriptor = ART_STYLE_DESCRIPTORS.get(series.art_style, series.art_style)
    custom_line = ""
    if series.custom_niche:
        custom_line = f'Topic area: {series.custom_niche}.\n'
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(niche=niche)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        niche=niche,
        art_style_descriptor=art_style_descriptor,
        custom_line=custom_line,
    )
    return system_prompt, user_prompt


def generate_script(series: Series, settings: AppSettings) -> GeneratedScript:
    if settings.script_provider == "ollama":
        return _generate_ollama(series, settings)
    elif settings.script_provider == "gemini":
        return _generate_gemini(series, settings)
    elif settings.script_provider == "openai":
        return _generate_openai(series, settings)
    else:
        raise ValueError(f"Unknown script provider: {settings.script_provider}")


def _generate_ollama(series, settings) -> GeneratedScript:
    import httpx

    system_prompt, user_prompt = _build_prompts(series)
    try:
        response = httpx.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "format": "json",
            },
            timeout=120.0,
        )
    except Exception as e:
        raise RuntimeError(
            f"Ollama not running at {settings.ollama_url}. Run: ollama serve ({e})"
        )
    response.raise_for_status()
    raw = response.json()["message"]["content"]
    return _parse_script_json(raw)


def _generate_gemini(series, settings) -> GeneratedScript:
    import google.generativeai as genai

    system_prompt, user_prompt = _build_prompts(series)
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content(
        system_prompt + "\n\n" + user_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json"
        ),
    )
    return _parse_script_json(result.text)


def _generate_openai(series, settings) -> GeneratedScript:
    from openai import OpenAI

    system_prompt, user_prompt = _build_prompts(series)
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return _parse_script_json(response.choices[0].message.content)


def _parse_script_json(raw: str) -> GeneratedScript:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    scenes = [
        SceneScript(
            scene_number=s["scene_number"],
            narration=s["narration"],
            image_prompt=s["image_prompt"],
            duration_hint=int(len(s["narration"].split()) / 2.5),
        )
        for s in data["scenes"]
    ]
    return GeneratedScript(title=data["title"], topic=data["topic"], scenes=scenes)
