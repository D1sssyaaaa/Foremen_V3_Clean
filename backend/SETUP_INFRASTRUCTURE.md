# УСТАНОВКА ИНФРАСТРУКТУРЫ

## ПРОБЛЕМА
Docker и PostgreSQL не установлены в системе.

## ВАРИАНТЫ РЕШЕНИЯ

### Вариант 1: Docker Desktop (РЕКОМЕНДУЕТСЯ)
1. Скачать Docker Desktop для Windows: https://www.docker.com/products/docker-desktop
2. Установить и запустить Docker Desktop
3. Выполнить команды:
```powershell
cd "c:\Users\milena\Desktop\new 2\backend"
docker compose up -d postgres redis minio
```

### Вариант 2: PostgreSQL Standalone
1. Скачать PostgreSQL 15: https://www.postgresql.org/download/windows/
2. Установить с параметрами:
   - Port: 5432
   - Password: postgres
   - Database: postgres
3. Создать БД:
```sql
CREATE DATABASE construction_costs;
```

## ТЕКУЩИЙ СТАТУС
- ❌ Docker не установлен
- ❌ PostgreSQL не установлен
- ✅ Backend API работает (7 модулей)
- ✅ Сервер запущен на http://localhost:8000

## РАБОТА БЕЗ БД
Можно продолжить разработку:
- ✅ Telegram Bot (не требует БД для базовой структуры)
- ✅ Модуль уведомлений (базовый код)
- ✅ FSM состояния для бота
- ⏳ Тесты API (можно с моками)

После установки PostgreSQL:
- Применить миграции: `alembic upgrade head`
- Протестировать с реальной БД
- Развернуть MinIO для УПД
