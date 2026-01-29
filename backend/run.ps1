# Быстрый запуск для разработки

# 1. Установка зависимостей (если еще не установлены)
# pip install -r requirements.txt

# 2. Запуск Docker
Write-Host "Запуск Docker..." -ForegroundColor Green
docker-compose up -d
Start-Sleep -Seconds 5

# 3. Применение миграций (если есть)
Write-Host "Применение миграций..." -ForegroundColor Green
alembic upgrade head

# 4. Запуск API
Write-Host "Запуск FastAPI..." -ForegroundColor Green
Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
python main.py
