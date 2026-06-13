# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for FacelessAI — builds a single clickable executable.

Build (on the target OS — PyInstaller does NOT cross-compile):
    pip install -r requirements.txt -r requirements-desktop.txt pyinstaller
    pyinstaller --noconfirm FacelessAI.spec
Result: dist/FacelessAI(.exe)

Optional providers (Gemini / OpenAI / ElevenLabs) and the local Kokoro voice
are bundled automatically *only if their packages are installed in the build
environment*. Install requirements-optional.txt and/or kokoro before building
to include them. ffmpeg, Ollama, and AUTOMATIC1111 remain external.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("frontend", "frontend")]
binaries = []
hiddenimports = []


def _collect(pkg):
    global datas, binaries, hiddenimports
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
        return True
    except Exception:
        return False


# Core runtime — always bundled.
for _pkg in ("uvicorn", "webview", "anyio", "sqlmodel", "httpx", "requests", "pytz"):
    _collect(_pkg)

hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("apscheduler")
hiddenimports += collect_submodules("fastapi")

# Optional / heavy providers — bundled only when present in the build env.
for _pkg in ("google.generativeai", "openai", "elevenlabs", "soundfile", "numpy", "scipy", "kokoro"):
    _collect(_pkg.split(".")[0])

block_cipher = None

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FacelessAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # set True to see a debug console if launch fails
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # set to "icon.ico" to brand the executable
)
