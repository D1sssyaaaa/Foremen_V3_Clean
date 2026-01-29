# Start All Servers

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   С ССТЫ" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] роверка портов..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }

if ($port8000) {
    Write-Host "   орт 8000 занят" -ForegroundColor Red
    exit 1
}

if ($port3000) {
    Write-Host "   орт 3000 занят" -ForegroundColor Red
    exit 1
}

Write-Host "   OK орты свободны" -ForegroundColor Green
Write-Host ""

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[2/4] апуск Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\backend'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
Start-Sleep -Seconds 3
Write-Host "   OK Backend запущен" -ForegroundColor Green
Write-Host ""

Write-Host "[3/4] апуск Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\frontend'; npm run dev"
Start-Sleep -Seconds 3
Write-Host "   OK Frontend запущен" -ForegroundColor Green
Write-Host ""

Write-Host "[4/4] апуск Bot..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootDir\backend'; python -m app.bot.main"
Start-Sleep -Seconds 2
Write-Host "   OK Bot запущен" -ForegroundColor Green
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "   OK С ССЫ ЩЫ" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "Docs:      http://localhost:8000/docs" -ForegroundColor White
Write-Host ""