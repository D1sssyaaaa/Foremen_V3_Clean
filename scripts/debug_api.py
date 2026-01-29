import asyncio
import httpx
import requests

API_URL = "http://localhost:8000/api/v1"

# Данные для входа (из load_test_data.py)
USERNAME = "admin"
PASSWORD = "admin123"

def debug_request():
    print("🔑 Авторизация...")
    try:
        auth_response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
        )
        auth_response.raise_for_status()
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Авторизация успешна")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return

    print("📡 Запрос к /objects...")
    try:
        response = requests.get(f"{API_URL}/objects", headers=headers)
        if response.status_code == 200:
            objects = response.json()
            print(f"✅ Объекты ({len(objects)}):")
            for obj in objects:
                print(f" - {obj['name']} (ID: {obj.get('id')})")
        else:
            print(f"❌ Ошибка {response.status_code}:")
            print(response.text)
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    except Exception as e:
        print(f"❌ Исключение при запросе: {e}")

if __name__ == "__main__":
    debug_request()
