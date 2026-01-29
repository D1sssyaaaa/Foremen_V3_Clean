#!/usr/bin/env python3
"""
Диагностический скрипт для проверки проблемы с /request-access командой
"""
import asyncio
import httpx
import sqlite3
from pathlib import Path

# Конфигурация
API_BASE_URL = "http://localhost:8000/api/v1"
DB_PATH = Path(__file__).parent / "construction_costs.db"

async def check_db():
    """Проверить объекты в БД"""
    print("\n" + "="*60)
    print("📊 ПРОВЕРКА БД")
    print("="*60)
    
    if not DB_PATH.exists():
        print(f"❌ БД не найдена: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Проверить таблицы
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cur.fetchall()
    print(f"\n✓ Всего таблиц: {len(tables)}")
    
    # Проверить cost_objects
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM cost_objects")
        count = cur.fetchone()['cnt']
        print(f"✓ cost_objects: {count} записей")
        
        if count > 0:
            cur.execute("SELECT id, name, code, status FROM cost_objects LIMIT 5")
            rows = cur.fetchall()
            print("\n  Примеры объектов:")
            for row in rows:
                print(f"    - ID {row['id']}: {row['code']} - {row['name']} ({row['status']})")
        else:
            print("  ⚠️  Нет объектов в БД!")
    except Exception as e:
        print(f"❌ Ошибка при проверке cost_objects: {e}")
    
    # Проверить users
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM users")
        count = cur.fetchone()['cnt']
        print(f"\n✓ users: {count} записей")
        
        if count > 0:
            cur.execute("SELECT id, username, roles FROM users LIMIT 3")
            rows = cur.fetchall()
            print("  Примеры пользователей:")
            for row in rows:
                print(f"    - ID {row['id']}: {row['username']} ({row['roles']})")
    except Exception as e:
        print(f"❌ Ошибка при проверке users: {e}")
    
    conn.close()

async def check_api_objects(token=None):
    """Проверить API endpoint /objects/"""
    print("\n" + "="*60)
    print("🔌 ПРОВЕРКА API /objects/")
    print("="*60)
    
    try:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_BASE_URL}/objects/", headers=headers)
        
        print(f"✓ Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Объектов в ответе: {len(data)}")
            if data:
                print("\n  Первые объекты:")
                for obj in data[:3]:
                    print(f"    - ID {obj.get('id')}: {obj.get('code')} - {obj.get('name')}")
            else:
                print("  ⚠️  Пустой ответ от API!")
        else:
            print(f"❌ Ошибка: {response.text}")
    
    except Exception as e:
        print(f"❌ Ошибка при вызове API: {e}")

async def check_api_auth():
    """Проверить получение токена"""
    print("\n" + "="*60)
    print("🔑 ПРОВЕРКА АВТОРИЗАЦИИ")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Попыт логина с тестовым пользователем
            response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={"username": "admin", "password": "admin"},
                headers={"Content-Type": "application/json"}
            )
        
        print(f"✓ Статус /auth/login: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✓ Токен получен: {token[:20]}...")
            return token
        else:
            print(f"⚠️  Не удалось авторизоваться: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return None

async def main():
    print("\n🔍 ДИАГНОСТИКА ПРОБЛЕМЫ '/request-access'")
    print("="*60)
    
    # 1. Проверить БД
    await check_db()
    
    # 2. Проверить API без токена
    print("\n⏳ Проверка API без токена...")
    await check_api_objects()
    
    # 3. Получить токен и повторить
    print("\n⏳ Получение токена для авторизованного доступа...")
    token = await check_api_auth()
    
    if token:
        print("\n⏳ Проверка API с токеном...")
        await check_api_objects(token)
    
    print("\n" + "="*60)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("="*60)
    print("\n📝 Рекомендации:")
    print("1. Если в БД нет объектов - создайте их через API или скрипт seed_data.py")
    print("2. Если API возвращает пустой список - проверьте фильтры в router.py")
    print("3. Если вызов без токена падает - объекты могут быть скрыты для неавториз. доступа")

if __name__ == "__main__":
    asyncio.run(main())
