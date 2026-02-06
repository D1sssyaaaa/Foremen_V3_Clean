# Restart All Servers - Construction Costs Management System

Write-Host "================================================" -ForegroundColor Magenta
Write-Host "   С ССТЫ" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "Шаг 1: становка..." -ForegroundColor Yellow
& "$PSScriptRoot\stop_all.ps1"

Write-Host "жидание 5 сек..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Шаг 2: апуск..." -ForegroundColor Yellow
& "$PSScriptRoot\start_all.ps1"

Write-Host ""
Write-Host "OK С Ш" -ForegroundColor Green
