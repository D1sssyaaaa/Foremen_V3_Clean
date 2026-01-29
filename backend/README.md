# Construction Costs Management System - Backend

Система учета затрат строительной компании.

## Технологический стек

- **Python 3.11+**
- **FastAPI** - асинхронный веб-фреймворк
- **PostgreSQL 15** - основная БД
- **Redis 7** - кэширование
- **MinIO** - хранилище XML файлов (S3-compatible)
- **SQLAlchemy 2.0** - ORM с async поддержкой
- **Alembic** - миграции БД
- **aiogram** - Telegram Bot

## Быстрый старт

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/Mac)
source .venv/bin/activate

# Установка пакетов
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
# Копировать пример конфига
cp .env.example .env

# Отредактировать .env под свои нужды
```

### 3. Запуск инфраструктуры (Docker)

```bash
# Запуск PostgreSQL, Redis, MinIO
docker-compose up -d

# Проверка статуса
docker-compose ps
```

Доступ к сервисам:
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)
- **MinIO API**: localhost:9000

### 4. Миграции БД

```bash
# Создание первой миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

### 5. Запуск приложения

```bash
# Development режим с hot-reload
python main.py

# Или через uvicorn напрямую
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API доступен по адресу:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Структура проекта

```
backend/
├── app/
│   ├── auth/          # Аутентификация, JWT, RBAC
│   ├── users/         # Пользователи, роли
│   ├── objects/       # Объекты учета
│   ├── time_sheets/   # Табели РТБ
│   ├── equipment/     # Заявки на технику
│   ├── materials/     # Заявки на материалы
│   ├── upd/           # УПД, парсинг XML
│   ├── analytics/     # Отчеты, аналитика
│   ├── notifications/ # Telegram Bot, уведомления
│   ├── core/          # Конфигурация, БД, базовые модели
│   └── models.py      # Модели SQLAlchemy
├── migrations/        # Alembic миграции
├── tests/             # Тесты
├── main.py            # Точка входа FastAPI
├── docker-compose.yml # Инфраструктура
└── requirements.txt   # Зависимости
```

## Разработка

### Создание нового модуля

Каждый модуль содержит:
- `models.py` - модели данных (если нужны специфичные)
- `schemas.py` - Pydantic схемы для валидации
- `router.py` - FastAPI роутеры
- `service.py` - бизнес-логика
- `dependencies.py` - зависимости (RBAC и т.д.)

### Миграции

```bash
# Автогенерация миграции после изменения моделей
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Просмотр истории
alembic history

# Откат на конкретную версию
alembic downgrade <revision>
```

### Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=app --cov-report=html

# Конкретный модуль
pytest tests/test_auth.py -v
```

## API Документация

### Основные группы эндпоинтов

- **/api/v1/auth** - Аутентификация (login, register, refresh)
- **/api/v1/users** - Управление пользователями
- **/api/v1/objects** - Объекты учета
- **/api/v1/time-sheets** - Табели РТБ
- **/api/v1/equipment-orders** - Аренда техники
- **/api/v1/material-requests** - Заявки на материалы
- **/api/v1/material-costs** - УПД, распределение
- **/api/v1/analytics** - Отчеты, аналитика
- **/api/v1/telegram** - Telegram Bot webhooks

Полная документация доступна по адресу `/docs` после запуска сервера.

## Переменные окружения

Основные переменные (см. `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO/S3
S3_ENDPOINT=localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=upd-documents

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://domain.com/api/v1/telegram/webhook
```

## Безопасность

- JWT токены для аутентификации
- RBAC (Role-Based Access Control) для авторизации
- Валидация всех входных данных через Pydantic
- Rate limiting на критичных endpoint-ах
- SQL injection protection через SQLAlchemy ORM
- Санитизация XML при загрузке УПД

## Производство (Production)

### Docker deployment

```bash
# Сборка образа
docker build -t construction-api:latest .

# Запуск с docker-compose
docker-compose up -d
```

### Переменные окружения для production

- Установить `ENVIRONMENT=production`
- Установить `DEBUG=False`
- Изменить `SECRET_KEY` на криптографически стойкий
- Настроить реальные credentials для PostgreSQL, Redis, MinIO
- Настроить HTTPS
- Настроить мониторинг и логирование

## Лицензия

Proprietary - все права защищены.
