#!/usr/bin/env python3
"""
Тестирование API управления доступом к объектам
"""
import asyncio
import aiohttp
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"

# Тестовые пользователи
USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "manager": {"username": "manager", "password": "manager123"},
    "foreman": {"username": "foreman", "password": "foreman123"},
}


class APIClient:
    def __init__(self):
        self.tokens = {}
    
    async def login(self, username: str, password: str) -> str:
        """Получить JWT токен"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/auth/login",
                json={"username": username, "password": password}
            ) as resp:
                data = await resp.json()
                token = data.get("access_token")
                self.tokens[username] = token
                return token
    
    async def request(
        self,
        method: str,
        endpoint: str,
        username: str = "admin",
        json_data: Optional[dict] = None
    ):
        """Выполнить запрос к API"""
        token = self.tokens.get(username)
        if not token:
            await self.login(USERS[username]["username"], USERS[username]["password"])
            token = self.tokens[username]
        
        headers = {"Authorization": f"Bearer {token}"}
        if json_data:
            headers["Content-Type"] = "application/json"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f"{BASE_URL}{endpoint}",
                headers=headers,
                json=json_data
            ) as resp:
                content = await resp.text()
                try:
                    data = json.loads(content)
                except:
                    data = content
                
                return {
                    "status": resp.status,
                    "data": data
                }


async def test_create_object():
    """Тест: Создание нового объекта"""
    print("\n📋 ТЕСТ 1: Создание нового объекта")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как менеджер
    await client.login("manager", "manager123")
    
    # Создание объекта
    response = await client.request(
        "POST",
        "/objects",
        username="manager",
        json_data={
            "name": "Жилой комплекс 'Солнечный'",
            "contract_number": "К-2025-001",
            "material_amount": 2000000,
            "labor_amount": 1000000
        }
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        obj_id = response['data'].get('id')
        print(f"✅ Создан объект ID: {obj_id}")
        print(f"✅ Код: {response['data'].get('code')}")
        return obj_id
    else:
        print(f"❌ Ошибка: {response['data']}")
        return None


async def test_foreman_request_access(object_id: int):
    """Тест: Бригадир запрашивает доступ"""
    print("\n📋 ТЕСТ 2: Бригадир запрашивает доступ к объекту")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как бригадир
    await client.login("foreman", "foreman123")
    
    # Запрос доступа
    response = await client.request(
        "POST",
        f"/objects/{object_id}/request-access",
        username="foreman",
        json_data={
            "reason": "Назначен ответственным за электромонтажные работы"
        }
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        req_id = response['data'].get('id')
        print(f"✅ Создан запрос ID: {req_id}")
        print(f"✅ Статус запроса: {response['data'].get('status')}")
        return req_id
    else:
        print(f"❌ Ошибка: {response['data']}")
        return None


async def test_foreman_get_my_requests():
    """Тест: Бригадир видит свои запросы"""
    print("\n📋 ТЕСТ 3: Получение моих запросов на доступ")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как бригадир
    await client.login("foreman", "foreman123")
    
    # Получение запросов
    response = await client.request(
        "GET",
        "/objects/access-requests/my",
        username="foreman"
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        requests = response['data']
        print(f"✅ Найдено запросов: {len(requests)}")
        for req in requests:
            print(f"   - Объект: {req.get('object_name')} (статус: {req.get('status')})")
    else:
        print(f"❌ Ошибка: {response['data']}")


async def test_manager_view_requests(object_id: int):
    """Тест: Менеджер видит все запросы к объекту"""
    print("\n📋 ТЕСТ 4: Менеджер видит все запросы к объекту")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как менеджер
    await client.login("manager", "manager123")
    
    # Получение запросов
    response = await client.request(
        "GET",
        f"/objects/{object_id}/access-requests",
        username="manager"
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        requests = response['data']
        print(f"✅ Найдено запросов: {len(requests)}")
        for req in requests:
            print(f"   - Бригадир: {req.get('foreman_name')}")
            print(f"     Статус: {req.get('status')}")
            print(f"     Причина: {req.get('reason')}")
        
        if requests:
            return requests[0]['id']
    else:
        print(f"❌ Ошибка: {response['data']}")
    
    return None


async def test_manager_approve_request(object_id: int, request_id: int):
    """Тест: Менеджер одобрет запрос"""
    print("\n📋 ТЕСТ 5: Менеджер одобряет запрос на доступ")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как менеджер
    await client.login("manager", "manager123")
    
    # Одобрение запроса
    response = await client.request(
        "POST",
        f"/objects/{object_id}/access-requests/{request_id}/approve",
        username="manager"
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        print(f"✅ Запрос одобрен")
        print(f"✅ Сообщение: {response['data'].get('message')}")
    else:
        print(f"❌ Ошибка: {response['data']}")


async def test_manager_reject_request(object_id: int, request_id: int):
    """Тест: Менеджер отклоняет запрос"""
    print("\n📋 ТЕСТ 6: Менеджер отклоняет запрос на доступ")
    print("-" * 50)
    
    client = APIClient()
    
    # Логин как менеджер
    await client.login("manager", "manager123")
    
    # Отклонение запроса
    response = await client.request(
        "POST",
        f"/objects/{object_id}/access-requests/{request_id}/reject",
        username="manager",
        json_data={
            "rejection_reason": "На объекте уже назначена основная бригада для этих работ"
        }
    )
    
    print(f"✅ Статус: {response['status']}")
    if response['status'] == 200:
        print(f"✅ Запрос отклонен")
        print(f"✅ Сообщение: {response['data'].get('message')}")
    else:
        print(f"❌ Ошибка: {response['data']}")


async def main():
    """Основная функция тестирования"""
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ API УПРАВЛЕНИЯ ДОСТУПОМ К ОБЪЕКТАМ")
    print("=" * 50)
    
    # Тест 1: Создание объекта
    object_id = await test_create_object()
    if not object_id:
        print("❌ Не удалось создать объект")
        return
    
    # Тест 2: Запрос доступа
    request_id = await test_foreman_request_access(object_id)
    if not request_id:
        print("❌ Не удалось создать запрос на доступ")
        return
    
    # Тест 3: Просмотр своих запросов
    await test_foreman_get_my_requests()
    
    # Тест 4: Менеджер видит запросы
    req_id = await test_manager_view_requests(object_id)
    if not req_id:
        print("❌ Не удалось получить запросы")
        return
    
    # Тест 5: Одобрение запроса
    await test_manager_approve_request(object_id, req_id)
    
    # Тест 6: Тест отклонения (на втором запросе)
    request_id_2 = await test_foreman_request_access(object_id)
    if request_id_2:
        req_id_2 = await test_manager_view_requests(object_id)
        if req_id_2 and req_id_2 != req_id:
            await test_manager_reject_request(object_id, req_id_2)
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
