@echo off
cd /d "%~dp0"
echo Stopping existing Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting server WITHOUT auto-reload...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug
