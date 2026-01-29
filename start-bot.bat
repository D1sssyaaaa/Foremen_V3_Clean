@echo off
echo ========================================
echo   Telegram Bot - Construction Costs
echo ========================================
echo.
echo Starting bot...
echo.

cd backend
call .venv\Scripts\activate.bat
python -m app.bot.main

pause
