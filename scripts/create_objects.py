
import requests
import sys

# Настройки
API_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Ошибка входа: {e}")
        try:
            print(response.text)
        except:
            pass
        sys.exit(1)

def create_object(token, name, code, address=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": name,
        "code": code,
        "address": address or "Адрес не указан",
        "is_active": True
    }
    
    print(f"🚀 Создание объекта '{name}' ({code})...")
    try:
        response = requests.post(f"{API_URL}/objects", headers=headers, json=data)
        if response.status_code in [200, 201]:
            print(f"✅ Создан: {response.json()['id']}")
        elif response.status_code == 422:
            print(f"❌ Ошибка валидации: {response.text}")
        elif response.status_code == 400 and "already exists" in response.text:
             print("⚠️ Уже существует")
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")

def main():
    token = login()
    create_object(token, "ЖК Северный", "NORD-001", "ул. Ленина 1")
    create_object(token, "Офис", "OFFICE-001", "ул. Мира 10")
    create_object(token, "Склад", "STORE-001", "ул. Промышленная 5")

if __name__ == "__main__":
    main()
