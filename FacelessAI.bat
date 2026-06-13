@echo off
REM Double-click launcher for FacelessAI (Windows).
REM Starts the app in a native desktop window.
cd /d "%~dp0"
python desktop.py
if errorlevel 1 (
    echo.
    echo FacelessAI exited with an error. See the message above.
    pause
)
