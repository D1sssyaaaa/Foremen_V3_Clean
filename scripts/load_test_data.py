
import os
import sys
import requests
import glob

# Настройки
API_URL = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"
XML_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "xml")

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
        sys.exit(1)

def get_first_object(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/objects/", headers=headers)
    if response.status_code == 200:
        objects = response.json()
        if objects:
            return objects[0]
    return None

def upload_xml(token, file_path):
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": open(file_path, "rb")}
    try:
        response = requests.post(f"{API_URL}/material-costs/upload", headers=headers, files=files)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 400 and "already exists" in response.text:
             print(f"Файл {os.path.basename(file_path)} уже загружен.")
             return None
        else:
            print(f"Ошибка загрузки {file_path}: {response.text}")
            return None
    except Exception as e:
        print(f"Ошибка запроса загрузки: {e}")
        return None

def distribute_upd(token, upd_id, object_id, amount):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "distributions": [
            {
                "cost_object_id": object_id,
                "distributed_amount": amount
            }
        ]
    }
    try:
        response = requests.post(f"{API_URL}/material-costs/{upd_id}/distribute", headers=headers, json=data)
        if response.status_code == 200:
            print(f"УПД {upd_id} успешно распределен на объект {object_id}")
            return True
        else:
            print(f"Ошибка распределения: {response.text}")
            return False
    except Exception as e:
        print(f"Ошибка запроса распределения: {e}")
        return False

def main():
    print("🔑 Авторизация...")
    token = login()
    print("✅ Успешно")

    print("🏗️ Поиск объектов...")
    obj = get_first_object(token)
    if not obj:
        print("❌ Объекты не найдены. Создайте объект в системе.")
        sys.exit(1)
    
    print(f"✅ Выбран объект: {obj['name']} (ID: {obj['id']})")

    xml_files = glob.glob(os.path.join(XML_DIR, "*.xml"))
    if not xml_files:
        print("❌ XML файлы не найдены в папке xml/")
        sys.exit(1)

    xml_files = glob.glob(os.path.join(XML_DIR, "*.xml"))
    if not xml_files:
        print("❌ XML файлы не найдены в папке xml/")
        sys.exit(1)

    # Перебираем файлы пока не получится загрузить
    success = False
    for xml_file in xml_files:
        print(f"📄 Попытка загрузки: {os.path.basename(xml_file)}")
        
        upd = upload_xml(token, xml_file)
        
        if upd:
            print(f"✅ УПД загружен: ID {upd['id']}, Сумма {upd['total_with_vat']}")
            
            # Распределяем
            print(f"🔄 Распределение на объект {obj['name']}...")
            if distribute_upd(token, upd['id'], obj['id'], upd['total_with_vat']):
                success = True
                break
        else:
            print("⚠️ Не удалось загрузить файл, переходим к следующему...")
            
    if not success:
        print("❌ Не удалось загрузить ни один XML файл.")

if __name__ == "__main__":
    main()
