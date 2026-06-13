@echo off
REM Build a standalone FacelessAI.exe on Windows.
REM Run this on the machine where you want the .exe (PyInstaller does not cross-compile).
cd /d "%~dp0"

echo Installing build dependencies...
python -m pip install -r requirements.txt -r requirements-desktop.txt pyinstaller
if errorlevel 1 goto fail

REM To bundle Gemini/OpenAI/ElevenLabs, uncomment the next line before building:
REM python -m pip install -r requirements-optional.txt

echo Building executable...
python -m PyInstaller --noconfirm FacelessAI.spec
if errorlevel 1 goto fail

echo.
echo Done. Your app is at:  dist\FacelessAI.exe
echo Double-click it to launch FacelessAI.
pause
exit /b 0

:fail
echo.
echo Build failed. See the output above.
pause
exit /b 1
