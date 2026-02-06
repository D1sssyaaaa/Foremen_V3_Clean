# Запуск Telegram Бота
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Telegram Bot - Construction Costs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка .env
$envFile = "backend\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "[ERROR] Файл .env не найден!" -ForegroundColor Red
    Write-Host "Скопируйте backend\.env.example в backend\.env и настройте TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    exit 1
}

# Проверка токена
$envContent = Get-Content $envFile -Raw
if ($envContent -notmatch "TELEGRAM_BOT_TOKEN=.+") {
    Write-Host "[WARNING] TELEGRAM_BOT_TOKEN не настроен в .env" -ForegroundColor Yellow
    Write-Host "Пожалуйста, добавьте токен от @BotFather" -ForegroundColor Yellow
    $continue = Read-Host "Продолжить без токена? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

Write-Host "[INFO] Активация виртуального окружения..." -ForegroundColor Green
Set-Location backend
& .\.venv\Scripts\Activate.ps1

Write-Host "[INFO] Запуск бота..." -ForegroundColor Green
Write-Host ""
python -m app.bot.main

Set-Location ..
