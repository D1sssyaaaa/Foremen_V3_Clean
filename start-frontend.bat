@echo off
chcp 65001 >nul
title Frontend Server - Construction Costs Management System
color 0B

echo ========================================
echo 🚀 Запуск Frontend сервера...
echo ========================================
echo.

cd /d "%~dp0frontend"

echo 📦 Запуск React + Vite сервера разработки
echo 🌐 Приложение будет доступно на: http://localhost:3000
echo.
echo ⚠️  Для остановки сервера нажмите Ctrl+C
echo ========================================
echo.

call npm run dev

pause
