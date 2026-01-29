# Скрипт запуска инфраструктуры для Windows
# PowerShell скрипт

Write-Host "🚀 Запуск инфраструктуры Construction Cost System..." -ForegroundColor Green

# Проверка наличия Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker не установлен. Установите Docker Desktop." -ForegroundColor Red
    exit 1
}

# Переход в директорию backend
Set-Location "$PSScriptRoot\..\backend"

# Проверка наличия .env файла
if (-not (Test-Path .env)) {
    Write-Host "📝 Создание .env файла из .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Пожалуйста, отредактируйте .env файл перед продолжением!" -ForegroundColor Yellow
    Write-Host "   Особенно измените SECRET_KEY и TELEGRAM_BOT_TOKEN" -ForegroundColor Yellow
    Read-Host "Нажмите Enter когда закончите редактирование"
}

# Запуск Docker Compose
Write-Host "🐳 Запуск Docker контейнеров..." -ForegroundColor Cyan
docker-compose up -d postgres redis

# Ожидание готовности PostgreSQL
Write-Host "⏳ Ожидание готовности PostgreSQL..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
do {
    $attempt++
    $ready = docker-compose exec -T postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "   PostgreSQL еще не готов, ждем... ($attempt/$maxAttempts)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "❌ PostgreSQL не запустился за отведенное время" -ForegroundColor Red
    exit 1
}

Write-Host "✅ PostgreSQL готов!" -ForegroundColor Green

# Ожидание готовности Redis
Write-Host "⏳ Ожидание готовности Redis..." -ForegroundColor Yellow
$maxAttempts = 15
$attempt = 0
do {
    $attempt++
    $ready = docker-compose exec -T redis redis-cli ping 2>&1
    if ($LASTEXITCODE -eq 0) {
        break
    }
    Write-Host "   Redis еще не готов, ждем... ($attempt/$maxAttempts)" -ForegroundColor Gray
    Start-Sleep -Seconds 1
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "❌ Redis не запустился за отведенное время" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Redis готов!" -ForegroundColor Green

# Проверка статуса
Write-Host ""
Write-Host "📊 Статус сервисов:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "✨ Инфраструктура запущена успешно!" -ForegroundColor Green
Write-Host ""
Write-Host "📌 Доступные сервисы:" -ForegroundColor Cyan
Write-Host "   PostgreSQL: localhost:5432"
Write-Host "   Redis: localhost:6379"
Write-Host ""
Write-Host "🔧 Следующие шаги:" -ForegroundColor Yellow
Write-Host "   1. Активируйте виртуальное окружение: .venv\Scripts\Activate.ps1"
Write-Host "   2. Установите зависимости: pip install -r requirements.txt"
Write-Host "   3. Примените миграции: alembic upgrade head"
Write-Host "   4. Запустите backend: uvicorn app.main:app --reload"
