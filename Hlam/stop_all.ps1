# Stop All Servers - Construction Costs Management System

Write-Host "================================================" -ForegroundColor Red
Write-Host "   СТ ССТЫ" -ForegroundColor Red
Write-Host "================================================" -ForegroundColor Red
Write-Host ""

Write-Host "[1/2] становка процессов..." -ForegroundColor Yellow
Get-Process | Where-Object {
    $_.ProcessName -like "*python*" -or 
    $_.ProcessName -like "*node*" -or 
    $_.ProcessName -like "*uvicorn*"
} | ForEach-Object {
    Write-Host "   становка: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Write-Host "   OK роцессы остановлены" -ForegroundColor Green
Write-Host ""

Write-Host "[2/2] роверка портов..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

if ($port8000 -or $port3000) {
    Write-Host "   екоторые порты заняты" -ForegroundColor Yellow
} else {
    Write-Host "   OK се порты освобождены" -ForegroundColor Green
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "   OK ССЫ СТЫ" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
