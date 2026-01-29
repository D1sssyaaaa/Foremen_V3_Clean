"""Тестирование API endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url, expected_status=200):
    """Тест endpoint"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        status = "OK" if response.status_code == expected_status else "FAIL"
        print(f"[{status}] {name}: {response.status_code}")
        if response.status_code == 200 and response.text:
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"     -> Записей: {len(data)}")
                elif isinstance(data, dict):
                    keys = list(data.keys())[:3]
                    print(f"     -> Ключи: {keys}")
            except:
                pass
        return response.status_code == expected_status
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return False

print("\n=== Тестирование API ===\n")

# Базовые endpoints
test_endpoint("Корневой endpoint", "/")
test_endpoint("Health check", "/health")
test_endpoint("OpenAPI docs", "/docs", 200)

# Требуют авторизации (ожидаем 401/403)
print("\n--- Endpoints с авторизацией ---")
test_endpoint("Список пользователей", "/api/v1/auth/users", expected_status=401)
test_endpoint("Объекты учета", "/api/v1/objects", expected_status=401)
test_endpoint("Табели", "/api/v1/time-sheets", expected_status=401)
test_endpoint("Заявки на материалы", "/api/v1/material-requests", expected_status=401)
test_endpoint("Заявки на технику", "/api/v1/equipment-orders", expected_status=401)

print("\n=== Тестирование завершено ===\n")
