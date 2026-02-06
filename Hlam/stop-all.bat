@echo off
chcp 65001 >nul
title Stop All Servers
color 0C

echo ========================================
echo 🛑 Остановка всех серверов...
echo ========================================
echo.

echo Остановка Python (Backend)...
taskkill /F /IM python.exe /T 2>nul
if %errorlevel% equ 0 (
    echo ✅ Backend остановлен
) else (
    echo ⚠️  Backend процессы не найдены
)

echo.
echo Остановка Node.js (Frontend)...
taskkill /F /IM node.exe /T 2>nul
if %errorlevel% equ 0 (
    echo ✅ Frontend остановлен
) else (
    echo ⚠️  Frontend процессы не найдены
)

echo.
echo ========================================
echo ✅ Все серверы остановлены
echo ========================================
echo.

timeout /t 2 /nobreak >nul
