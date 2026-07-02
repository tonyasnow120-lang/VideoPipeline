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

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo NOTE: ffmpeg was not found on PATH. Transcription will not work
    echo until you install it:  winget install ffmpeg
    echo.
)

if not exist node_modules (
    echo First run - installing dependencies, this takes a minute...
    call npm install --no-audit --no-fund
    if errorlevel 1 (
        echo npm install failed. See the message above.
        pause
        exit /b 1
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
