"""
Скрипт инициализации базы данных
Создание таблиц и начальных данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine, Base
from app.core.models_base import *  # Импорт всех моделей
from app.models import *  # Импортируем все модели включая AuditLog
from app.core.config import settings


async def init_db():
    """Инициализация базы данных"""
    print("🔧 Начало инициализации базы данных...")
    
    # Определяем тип БД
    is_postgres = "postgresql" in settings.database_url
    is_sqlite = "sqlite" in settings.database_url
    
    if is_postgres:
        print(f"📊 Подключение к PostgreSQL: {settings.database_url.split('@')[-1]}")
    elif is_sqlite:
        db_file = settings.database_url.split(':///')[-1]
        print(f"📊 Используется SQLite: {db_file}")
    
    try:
        # Проверка подключения
        async with engine.begin() as conn:
            if is_postgres:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Подключение успешно!")
                print(f"📌 PostgreSQL версия: {version}")
            elif is_sqlite:
                result = await conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                print(f"✅ Подключение успешно!")
                print(f"📌 SQLite версия: {version}")
        
        # Создание всех таблиц
        print("\n🏗️  Создание таблиц...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Таблицы успешно созданы!")
        
        # Список созданных таблиц
        async with engine.begin() as conn:
            if is_postgres:
                result = await conn.execute(text("""
                    SELECT tablename 
                    FROM pg_catalog.pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """))
            elif is_sqlite:
                result = await conn.execute(text("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
            
            tables = result.fetchall()
            
            if tables:
                print(f"\n📋 Создано таблиц: {len(tables)}")
                for table in tables:
                    print(f"   ✓ {table[0]}")
            else:
                print("\n⚠️  Таблицы не найдены. Возможно, модели не импортированы.")
        
        print("\n✨ База данных успешно инициализирована!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при инициализации БД: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def check_connection():
    """Проверка подключения к БД"""
    print("🔍 Проверка подключения к базе данных...")
    print(f"📊 URL: {settings.database_url.split('://')[0]}://...")
    
    try:
        async with engine.begin() as conn:
            # Определяем тип БД
            if "postgresql" in settings.database_url:
                result = await conn.execute(text("SELECT current_database(), current_user"))
                db_name, user = result.fetchone()
                print(f"✅ PostgreSQL подключение успешно!")
                print(f"   База данных: {db_name}")
                print(f"   Пользователь: {user}")
            elif "sqlite" in settings.database_url:
                result = await conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                print(f"✅ SQLite подключение успешно!")
                print(f"   Версия SQLite: {version}")
                print(f"   Файл: {settings.database_url.split(':///')[-1]}")
            else:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
                print(f"✅ Подключение к БД успешно!")
            
            # Проверка Redis
            try:
                import redis.asyncio as redis  # type: ignore
                redis_client = redis.from_url(settings.redis_url)
                await redis_client.ping()
                print(f"✅ Redis доступен: {settings.redis_url}")
                await redis_client.close()
            except Exception as e:
                print(f"⚠️  Redis недоступен: {e}")
                print(f"   (Redis не обязателен для работы, используется для кэширования)")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    finally:
        await engine.dispose()


async def reset_db():
    """Полная очистка и пересоздание БД (ОСТОРОЖНО!)"""
    print("⚠️  ВНИМАНИЕ! Это удалит ВСЕ данные из базы!")
    response = input("Продолжить? (yes/NO): ")
    
    if response.lower() != 'yes':
        print("Операция отменена.")
        return
    
    print("\n🗑️  Удаление всех таблиц...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ Таблицы удалены")
        
        print("\n🏗️  Создание таблиц заново...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Таблицы созданы")
        
        print("\n✨ База данных сброшена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Управление базой данных")
    parser.add_argument(
        "command",
        choices=["init", "check", "reset"],
        help="Команда: init (создать таблицы), check (проверить подключение), reset (пересоздать БД)"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        asyncio.run(init_db())
    elif args.command == "check":
        asyncio.run(check_connection())
    elif args.command == "reset":
        asyncio.run(reset_db())
