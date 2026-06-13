# FacelessAI

Automatically generate faceless short-form videos for TikTok, Instagram Reels, and YouTube Shorts. Runs entirely on your machine — no mandatory subscriptions.

## Prerequisites

### Required
- Python 3.11+
- ffmpeg: `brew install ffmpeg` / `sudo apt install ffmpeg` / https://ffmpeg.org

### For free image generation (recommended)
- AUTOMATIC1111 Stable Diffusion WebUI running with `--api` flag
  - Install: https://github.com/AUTOMATIC1111/stable-diffusion-webui
  - Launch: `./webui.sh --api` (Linux/Mac) or `webui-user.bat --api` (Windows)
  - Requires a GPU with 8GB+ VRAM for comfortable speed
  - Without GPU: images generate slowly on CPU (~5–15 min each) but work fine for scheduled overnight generation

### For free script generation (recommended)
- Ollama: https://ollama.com
  - After installing: `ollama pull llama3.3:8b`

### No GPU? No Ollama?
- Use Google Gemini free API for scripts (free tier, requires Google account)
- Use OpenAI Images API for images (paid, ~$0.01–0.05/image)
- Voice (Kokoro) always runs free on CPU

## Setup

```bash
git clone <repo>
cd faceless-ai
pip install -r requirements.txt
python main.py
```

Open http://localhost:8000

Optional paid/alternative providers (ElevenLabs, OpenAI, Gemini):

```bash
pip install -r requirements-optional.txt
```

## Desktop App (Windows)

Run the dashboard in a native desktop window instead of a browser tab — no
terminal needed after setup.

```bash
pip install -r requirements-desktop.txt
```

Then **double-click `FacelessAI.bat`**. It starts the server in the background
and opens the dashboard in a native window. To make it feel like a real app,
right-click `FacelessAI.bat` → **Create shortcut**, then move the shortcut to
your Desktop or Start Menu (and optionally set a custom icon via the shortcut's
Properties → Change Icon).

Notes:
- pywebview uses the **Edge WebView2** runtime. It's preinstalled on Windows 11;
  on Windows 10 install it from
  https://developer.microsoft.com/microsoft-edge/webview2/.
- Python must be installed and on PATH. (This launcher does not bundle Python.)
- You can also launch it from a terminal with `python desktop.py`.

## First Steps
1. Go to **Settings** → configure your providers
2. Click **Refresh Status** to verify connections
3. Go to **Series** → **New Series** → follow the 4-step wizard
4. Go to **Generate** → select your series → **Generate Video**
5. Watch it build in real time, then download

## Adding Background Music
Add royalty-free MP3 files to `assets/music/`. Good free sources:
- **Pixabay Music**: https://pixabay.com/music (CC0, no attribution needed)
- **YouTube Audio Library**: studio.youtube.com → Music (safe for YouTube Shorts)
- **Free Music Archive**: https://freemusicarchive.org (filter by CC0)

**TikTok note:** Content ID on TikTok is aggressive. Consider uploading videos without baked-in music and using TikTok's built-in sound library instead.

## Cost Summary
| Component | Free path | Paid fallback |
|---|---|---|
| Scripts | Ollama local / Gemini free | OpenAI ~$0.008/video |
| Voice | Kokoro (local) | ElevenLabs ~$22+/mo |
| Images | AUTOMATIC1111 local | OpenAI Images ~$0.01–0.05/img |
| Video assembly | ffmpeg (free) | — |
