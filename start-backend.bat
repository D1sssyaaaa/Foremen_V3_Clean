@echo off
chcp 65001 >nul
title Backend Server - Construction Costs Management System
color 0A

echo ========================================
echo 🚀 Запуск Backend сервера...
echo ========================================
echo.

cd /d "%~dp0backend"

echo 📦 Используется Python из виртуального окружения
echo 🌐 Сервер будет доступен на: http://localhost:8000
echo 📖 API документация: http://localhost:8000/docs
echo.
echo ⚠️  Для остановки сервера нажмите Ctrl+C
echo ========================================
echo.

"%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
