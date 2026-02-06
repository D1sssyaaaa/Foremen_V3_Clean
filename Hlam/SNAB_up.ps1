<#
.SYNOPSIS
    SNAB_up - Script to manage Construction Costs System (Start/Stop/Restart)
#>

param (
    [string]$Action = ""
)

$RootPath = $PSScriptRoot
$BackendPath = Join-Path $RootPath "backend"

function Show-Menu {
    Clear-Host
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "      SNAB System Management             " -ForegroundColor Yellow
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "1. Start All (Docker + App)" -ForegroundColor Green
    Write-Host "2. Stop All" -ForegroundColor Red
    Write-Host "3. Restart All" -ForegroundColor Magenta
    Write-Host "4. Docker Only (Up)" -ForegroundColor Blue
    Write-Host "5. Docker Only (Down)" -ForegroundColor DarkBlue
    Write-Host "Q. Quit" -ForegroundColor Gray
    Write-Host "=========================================" -ForegroundColor Cyan
}

function Start-All {
    Write-Host "Starting SNAB System..." -ForegroundColor Green
    
    # 1. Docker
    Write-Host "Starting Docker containers..." -ForegroundColor Cyan
    Set-Location $BackendPath
    docker-compose up -d postgres redis minio
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start Docker." -ForegroundColor Red
        return
    }
    Write-Host "Waiting 10 seconds for databases to initialize..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 10
    
    # 2. Backend
    Write-Host "Starting Backend..." -ForegroundColor Cyan
    Set-Location $RootPath
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; [System.Console]::Title = 'SNAB Backend'; python main.py"
    Write-Host "Waiting 5 seconds for Backend to start..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 5
    
    # 3. Bot
    Write-Host "Starting Telegram Bot..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; [System.Console]::Title = 'SNAB Bot'; python -m app.bot.main"
    Write-Host "Waiting 3 seconds for Bot to start..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 3
    
    # 4. Frontend
    Write-Host "Starting Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", "cd frontend; [System.Console]::Title = 'SNAB Frontend'; npm run dev"
    
    Write-Host "All services launched!" -ForegroundColor Green
}

function Stop-All {
    Write-Host "Stopping SNAB System..." -ForegroundColor Yellow
    
    # Docker
    Write-Host "Stopping Docker containers..." -ForegroundColor Cyan
    Set-Location $BackendPath
    docker-compose stop
    
    Write-Host "Please close the Backend, Bot, and Frontend terminal windows manually." -ForegroundColor Yellow
    Write-Host "Docker stopped." -ForegroundColor Green
}

# Main Loop
if ($Action) {
    switch ($Action.ToLower()) {
        "start" { Start-All }
        "stop" { Stop-All }
        "restart" { Stop-All; Start-All }
        default { Write-Host "Unknown action." }
    }
}
else {
    while ($true) {
        Show-Menu
        $choice = Read-Host "Select an option"
        
        switch ($choice) {
            "1" { Start-All; Pause }
            "2" { Stop-All; Pause }
            "3" { Stop-All; Start-All; Pause }
            "4" { Set-Location $BackendPath; docker-compose up -d; Pause }
            "5" { Set-Location $BackendPath; docker-compose stop; Pause }
            "Q" { exit }
            "q" { exit }
            default { Write-Host "Invalid option." -ForegroundColor Red; Start-Sleep -Seconds 1 }
        }
    }
}
