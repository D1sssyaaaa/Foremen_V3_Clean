#!/bin/bash
# Скрипт запуска PostgreSQL и Redis в Docker

echo "🚀 Запуск инфраструктуры Construction Cost System..."

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и Docker Compose."
    exit 1
fi

# Переход в директорию backend
cd "$(dirname "$0")/../backend"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла из .env.example..."
    cp .env.example .env
    echo "⚠️  Пожалуйста, отредактируйте .env файл перед продолжением!"
    echo "   Особенно измените SECRET_KEY и TELEGRAM_BOT_TOKEN"
    read -p "Нажмите Enter когда закончите редактирование..."
fi

# Запуск Docker Compose
echo "🐳 Запуск Docker контейнеров..."
docker-compose up -d postgres redis

# Ожидание готовности PostgreSQL
echo "⏳ Ожидание готовности PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   PostgreSQL еще не готов, ждем..."
    sleep 2
done

echo "✅ PostgreSQL готов!"

# Ожидание готовности Redis
echo "⏳ Ожидание готовности Redis..."
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "   Redis еще не готов, ждем..."
    sleep 1
done

echo "✅ Redis готов!"

# Проверка статуса
echo ""
echo "📊 Статус сервисов:"
docker-compose ps

echo ""
echo "✨ Инфраструктура запущена успешно!"
echo ""
echo "📌 Доступные сервисы:"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🔧 Следующие шаги:"
echo "   1. Активируйте виртуальное окружение"
echo "   2. Установите зависимости: pip install -r requirements.txt"
echo "   3. Примените миграции: alembic upgrade head"
echo "   4. Запустите backend: uvicorn app.main:app --reload"
