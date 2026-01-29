@echo off
chcp 65001 >nul
title Construction Costs Management System - Full Launcher
color 0E

echo ========================================
echo 🚀 Система учета затрат "Снаб"
echo ========================================
echo.
echo 📋 Запуск всех компонентов...
echo.

cd /d "%~dp0"

echo 1️⃣  Запуск Backend сервера в отдельном окне...
start "Backend - http://localhost:8000" /D "%~dp0" "%~dp0start-backend.bat"

timeout /t 3 /nobreak >nul

echo 2️⃣  Запуск Frontend сервера в отдельном окне...
start "Frontend - http://localhost:3000" /D "%~dp0" "%~dp0start-frontend.bat"

timeout /t 3 /nobreak >nul

echo 3️⃣  Запуск Telegram Бота в отдельном окне...
start "Telegram Bot" /D "%~dp0" "%~dp0start-bot.bat"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo ✅ Все компоненты запущены!
echo ========================================
echo.
echo 🌐 Backend API:     http://localhost:8000
echo 📖 API Docs:        http://localhost:8000/docs
echo 🖥️  Frontend:        http://localhost:3000
echo 🤖 Telegram Bot:    Работает в фоне
echo.
echo 💡 Откроется браузер через 3 секунды...
echo.

timeout /t 3 /nobreak >nul
start http://localhost:3000

echo ========================================
echo 📌 Окно можно закрыть
echo    Все компоненты работают в отдельных окнах
echo.
echo Для остановки всех компонентов:
echo    Закройте все окна или используйте stop-all.bat
echo ========================================
echo.

pause
