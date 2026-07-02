@echo off
REM Double-click launcher for the Video Graphics Pipeline GUI (Windows).
REM Starts the dashboard server and opens it in your browser.
REM Keep this window open while you work; closing it stops the server.
cd /d "%~dp0remotion"

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js is not installed or not on PATH.
    echo Install it from https://nodejs.org and run this again.
    pause
    exit /b 1
)

for /f "tokens=1 delims=." %%v in ('node -v') do set NODEMAJOR=%%v
set NODEMAJOR=%NODEMAJOR:v=%
if %NODEMAJOR% LSS 18 (
    echo Your Node.js version is too old ^(need 18 or newer^).
    echo Install the current version from https://nodejs.org and run this again.
    pause
    exit /b 1
)

echo Checking dependencies (first run takes a minute)...
call npm install --no-audit --no-fund
if errorlevel 1 (
    echo npm install failed. See the message above.
    pause
    exit /b 1
)

REM FFmpeg comes bundled via npm (ffmpeg-static). Only warn if that download
REM failed AND there is no system-wide ffmpeg either.
if not exist node_modules\ffmpeg-static\ffmpeg.exe (
    where ffmpeg >nul 2>nul
    if errorlevel 1 (
        echo NOTE: ffmpeg is not available yet. Transcription will not work
        echo until you install it:  winget install ffmpeg
        echo Then close this window and run Pipeline.bat again.
        echo.
    )
)

if not exist .env (
    copy .env.example .env >nul
    echo Created remotion\.env - opening it so you can paste your OpenAI API key.
    echo Save and close Notepad, then the dashboard will start.
    notepad .env
)

node gui\server.mjs --open
if errorlevel 1 (
    echo.
    echo The pipeline GUI exited with an error. See the message above.
    pause
)
