#!/usr/bin/env python3
"""
Скрипт для тестирования исправленной команды /request-access
"""
import asyncio
import httpx
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"

async def test_objects_with_auth():
    """Протестировать получение объектов с авторизацией"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ: Получение объектов через API")
    print("="*60)
    
    token = None
    
    # Шаг 1: Логинимся
    print("\n1️⃣  Авторизация...")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/auth/telegram/login",
                json={"telegram_user_id": 123456789},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"   ✅ Токен получен: {token[:30]}...")
            elif response.status_code == 404:
                print("   ℹ️  Пользователь не зарегистрирован - используем тестового админа")
                # Логинимся как админ
                response = await client.post(
                    f"{API_BASE_URL}/auth/login",
                    json={"username": "admin", "password": "admin123"},
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 200:
                    token = response.json().get("access_token")
                    print(f"   ✅ Admin токен получен: {token[:30]}...")
                else:
                    print(f"   ❌ Ошибка авторизации: {response.status_code}")
                    print(f"   {response.text}")
                    return
            else:
                print(f"   ❌ Ошибка: {response.status_code}")
                print(f"   {response.text}")
                return
        except Exception as e:
            print(f"   ❌ Ошибка соединения: {e}")
            return
        
        # Шаг 2: Получаем объекты с токеном
        print("\n2️⃣  Получение объектов с авторизацией...")
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            response = await client.get(
                f"{API_BASE_URL}/objects/",
                headers=headers
            )
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Получено объектов: {len(data)}")
                
                if data:
                    print("\n   Объекты:")
                    for obj in data:
                        print(f"     • ID {obj.get('id')}: {obj.get('code')} - {obj.get('name')}")
                else:
                    print("   ⚠️  Список пуст!")
            else:
                print(f"   ❌ Ошибка: {response.text}")
        
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # Шаг 3: Тестируем с неправильным токеном
        print("\n3️⃣  Тест с невалидным токеном...")
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer INVALID_TOKEN"
            }
            response = await client.get(
                f"{API_BASE_URL}/objects/",
                headers=headers
            )
            
            print(f"   Статус: {response.status_code}")
            if response.status_code != 200:
                print(f"   ✅ Ожидаемо получена ошибка: {response.status_code}")
            else:
                print(f"   ⚠️  Неожиданно получен статус 200!")
        
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

async def main():
    print("\n" + "🤖 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ /request-access".center(60, "="))
    print("\nДиагностирование проблем:")
    print("1. Проверка авторизации")
    print("2. Проверка получения объектов")
    print("3. Проверка обработки токена\n")
    
    await test_objects_with_auth()
    
    print("\n" + "="*60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*60)
    print("\n📋 РЕЗУЛЬТАТЫ:")
    print("• Если объекты получены - проблема была в передаче токена")
    print("• Если объекты не получены - проверьте БД и статус сервера")
    print("• Если ошибка авторизации - проверьте конфиг и токены\n")

if __name__ == "__main__":
    asyncio.run(main())
