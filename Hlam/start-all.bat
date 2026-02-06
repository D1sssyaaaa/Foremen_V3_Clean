@echo off
chcp 65001 >nul
title Construction Costs Management System - Launcher
color 0E

echo ========================================
echo 🚀 Система учета затрат "Снаб"
echo ========================================
echo.
echo 📋 Запуск всех серверов...
echo.

cd /d "%~dp0"

echo 1️⃣  Запуск Backend сервера в отдельном окне...
start "Backend - http://localhost:8000" /D "%~dp0" "%~dp0start-backend.bat"

timeout /t 3 /nobreak >nul

echo 2️⃣  Запуск Frontend сервера в отдельном окне...
start "Frontend - http://localhost:3000" /D "%~dp0" "%~dp0start-frontend.bat"

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo ✅ Серверы запущены!
echo ========================================
echo.
echo 🌐 Backend API: http://localhost:8000
echo 📖 API Docs:    http://localhost:8000/docs
echo 🖥️  Frontend:    http://localhost:3000
echo.
echo 💡 Откроется браузер через 3 секунды...
echo.

timeout /t 3 /nobreak >nul
start http://localhost:3000

echo ========================================
echo 📌 Окно можно закрыть
echo    Серверы работают в отдельных окнах
echo ========================================
echo.

pause
