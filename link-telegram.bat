@echo off
echo ========================================
echo   Link Telegram ID to User
echo ========================================
echo.
echo Starting link script...
echo.

cd backend
call .venv\Scripts\activate.bat
python link_telegram.py

pause
