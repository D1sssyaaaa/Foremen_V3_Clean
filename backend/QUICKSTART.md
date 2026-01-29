# БЫСТРЫЙ ЗАПУСК БЕЗ DOCKER

## ⚠️ ВАЖНО: Для полноценной работы нужно установить:
1. **PostgreSQL 15** - скачать с https://www.postgresql.org/download/windows/
2. **Redis 7** - скачать с https://github.com/redis-windows/redis-windows/releases
3. **Docker Desktop** (рекомендуется) - https://www.docker.com/products/docker-desktop/

## Запуск без Docker (только для тестирования API)

Если нет Docker, можно запустить API в режиме разработки **БЕЗ базы данных** (только для проверки endpoint-ов):

```powershell
# В файле .env измените DATABASE_URL на SQLite (временно):
# DATABASE_URL=sqlite+aiosqlite:///./test.db

# Запуск приложения
cd "c:\Users\milena\Desktop\new 2\backend"
python main.py
```

API будет доступен по адресу: **http://localhost:8000**
Документация: **http://localhost:8000/docs**

## Установка PostgreSQL локально (Windows)

1. Скачать PostgreSQL 15: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
2. Установить с настройками:
   - Port: 5432
   - Password: postgres
   - Database: construction_costs (создать после установки)

3. После установки создать БД:
```powershell
psql -U postgres
CREATE DATABASE construction_costs;
\q
```

4. В .env убедиться что:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/construction_costs
```

## Запуск с PostgreSQL (без Docker)

```powershell
# 1. Создание миграций
cd "c:\Users\milena\Desktop\new 2\backend"
alembic revision --autogenerate -m "Initial migration"

# 2. Применение миграций
alembic upgrade head

# 3. Создание администратора
python create_admin.py

# 4. Запуск API
python main.py
```

## Проверка работы

1. Открыть http://localhost:8000/docs
2. Зарегистрировать пользователя через `/api/v1/auth/register`
3. Войти через `/api/v1/auth/login` и получить токены
4. Использовать access_token для доступа к защищенным endpoint-ам

## Тестирование через curl

```powershell
# Регистрация
$body = @{
    username = "testuser"
    password = "test123"
    phone = "+7-900-123-45-67"
    roles = @("FOREMAN")
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Вход
$loginBody = @{
    username = "testuser"
    password = "test123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method Post `
    -ContentType "application/json" `
    -Body $loginBody

$token = $response.access_token

# Получение профиля
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" `
    -Method Get `
    -Headers @{Authorization="Bearer $token"}
```

## ✅ Следующие шаги после запуска

1. Протестировать аутентификацию
2. Проверить RBAC (доступ по ролям)
3. Реализовать остальные модули
4. Интегрировать парсер УПД
5. Настроить Telegram Bot
