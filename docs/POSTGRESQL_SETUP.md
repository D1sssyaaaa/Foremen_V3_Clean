# Инструкция по установке PostgreSQL и Redis

## Вариант 1: Установка PostgreSQL и Redis локально (без Docker)

### Шаг 1: Установка PostgreSQL

1. **Скачайте PostgreSQL 15:**
   - Перейдите на https://www.postgresql.org/download/windows/
   - Скачайте PostgreSQL 15.x для Windows
   - Запустите установщик

2. **Во время установки:**
   - Установите пароль для пользователя `postgres` (например: `postgres`)
   - Порт: оставьте `5432`
   - Locale: выберите `Russian, Russia` или `Default locale`

3. **После установки:**
   - Откройте pgAdmin 4 (устанавливается вместе с PostgreSQL)
   - Создайте новую базу данных:
     - Название: `construction_costs`
     - Owner: `postgres`

### Шаг 2: Установка Redis (опционально для начала)

**Для Windows:**
Redis официально не поддерживает Windows, но есть порт от Microsoft:

1. Скачайте Redis для Windows:
   - https://github.com/microsoftarchive/redis/releases
   - Выберите `Redis-x64-3.0.504.msi` или новее
   - Установите с настройками по умолчанию

2. Redis запустится как служба Windows автоматически

**Альтернатива:** Можно временно работать без Redis, он нужен для кэширования.

---

## Вариант 2: Использование Docker Desktop (рекомендуется)

### Шаг 1: Установка Docker Desktop

1. **Скачайте Docker Desktop для Windows:**
   - https://www.docker.com/products/docker-desktop/
   - Скачайте и запустите установщик

2. **Требования:**
   - Windows 10/11 Pro, Enterprise или Education
   - WSL 2 (устанавливается автоматически)

3. **После установки:**
   - Запустите Docker Desktop
   - Дождитесь запуска (иконка в трее станет зелёной)

### Шаг 2: Запуск PostgreSQL и Redis

Откройте PowerShell в папке проекта и выполните:

```powershell
cd "C:\Users\milena\Desktop\new 2\backend"
docker-compose up -d postgres redis
```

Проверка статуса:
```powershell
docker-compose ps
```

---

## Вариант 3: Временное использование SQLite (для быстрого старта)

Если хотите начать работу прямо сейчас без установки PostgreSQL:

1. **Текущая БД SQLite уже работает**
2. **Код написан универсально** и поддерживает PostgreSQL
3. **Позже легко мигрировать** на PostgreSQL

### Что нужно сделать сейчас:

1. Убедитесь что `.env` файл существует:
```powershell
cd "C:\Users\milena\Desktop\new 2\backend"
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

2. Инициализируйте БД:
```powershell
python scripts/init_db.py check
```

3. Создайте таблицы:
```powershell
python scripts/init_db.py init
```

---

## Рекомендация

**Для обучения и разработки:**
- Используйте SQLite (уже настроено)
- Переходите на PostgreSQL когда понадобится production

**Для production:**
- Установите Docker Desktop (Вариант 2)
- Или установите PostgreSQL локально (Вариант 1)

---

## Что делать дальше?

После выбора варианта сообщите, и я помогу:
1. Создать и применить миграции БД
2. Запустить backend сервер
3. Протестировать подключение
