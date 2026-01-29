# Скрипт инициализации проекта
# Выполните команды последовательно

# 1. Запуск Docker инфраструктуры (PostgreSQL, Redis, MinIO)
Write-Host "Запуск Docker инфраструктуры..." -ForegroundColor Green
docker-compose up -d

# 2. Ожидание запуска сервисов
Write-Host "Ожидание запуска сервисов (10 секунд)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 3. Создание первой миграции
Write-Host "Создание первой миграции..." -ForegroundColor Green
alembic revision --autogenerate -m "Initial migration: all tables"

# 4. Применение миграций
Write-Host "Применение миграций к БД..." -ForegroundColor Green
alembic upgrade head

Write-Host "Инициализация завершена!" -ForegroundColor Green
Write-Host "Для запуска API выполните: python main.py" -ForegroundColor Cyan
