"""
Интерактивное тестирование API
"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_get(name, url):
    """GET запрос"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        print(f"[{response.status_code}] {name}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  -> Найдено записей: {len(data)}")
                if data:
                    print(f"  -> Первая запись: {json.dumps(data[0], ensure_ascii=False, indent=2)[:200]}...")
            elif isinstance(data, dict):
                print(f"  -> Данные: {json.dumps(data, ensure_ascii=False, indent=2)[:300]}")
        else:
            print(f"  -> {response.text[:100]}")
        return response
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return None

def test_post(name, url, data):
    """POST запрос"""
    try:
        response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        print(f"[{response.status_code}] {name}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"  -> Результат: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}")
        else:
            print(f"  -> {response.text[:200]}")
        return response
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return None

# ======================
# ТЕСТИРОВАНИЕ
# ======================

print_section("1. БАЗОВЫЕ ENDPOINTS")
test_get("Корневой endpoint", "/")
test_get("Health check", "/health")

print_section("2. АУТЕНТИФИКАЦИЯ")
# Попытка получить токен
login_data = {
    "username": "admin",
    "password": "admin123"
}
response = test_post("Логин (admin)", "/api/v1/auth/login", login_data)

if response and response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"\n✅ Токен получен: {access_token[:30]}...")
    
    # Заголовки с авторизацией
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print_section("3. ОБЪЕКТЫ УЧЕТА (с авторизацией)")
    r = requests.get(f"{BASE_URL}/api/v1/objects", headers=headers)
    print(f"[{r.status_code}] Список объектов")
    if r.status_code == 200:
        objects = r.json()
        print(f"  -> Всего объектов: {len(objects)}")
        for obj in objects[:3]:
            print(f"     • {obj.get('name')} ({obj.get('code')})")
    
    print_section("4. БРИГАДЫ")
    r = requests.get(f"{BASE_URL}/api/v1/time-sheets/brigades", headers=headers)
    print(f"[{r.status_code}] Список бригад")
    if r.status_code == 200:
        brigades = r.json()
        print(f"  -> Всего бригад: {len(brigades)}")
        for b in brigades:
            print(f"     • {b.get('name')} (ID: {b.get('id')})")
    
    print_section("5. ЗАЯВКИ НА МАТЕРИАЛЫ")
    r = requests.get(f"{BASE_URL}/api/v1/material-requests", headers=headers)
    print(f"[{r.status_code}] Список заявок")
    if r.status_code == 200:
        requests_list = r.json()
        print(f"  -> Всего заявок: {len(requests_list)}")
        if requests_list:
            req = requests_list[0]
            print(f"     • ID: {req.get('id')}, Статус: {req.get('status')}")
    
    print_section("6. ЗАЯВКИ НА ТЕХНИКУ")
    r = requests.get(f"{BASE_URL}/api/v1/equipment-orders", headers=headers)
    print(f"[{r.status_code}] Список заявок")
    if r.status_code == 200:
        orders = r.json()
        print(f"  -> Всего заявок: {len(orders)}")
        if orders:
            order = orders[0]
            print(f"     • {order.get('equipment_type')}, Статус: {order.get('status')}")
    
    print_section("7. АНАЛИТИКА")
    # Получить ID первого объекта
    r = requests.get(f"{BASE_URL}/api/v1/objects", headers=headers)
    if r.status_code == 200 and r.json():
        obj_id = r.json()[0]['id']
        
        # Затраты по объекту
        r = requests.get(
            f"{BASE_URL}/api/v1/analytics/objects/{obj_id}/costs",
            headers=headers,
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        )
        print(f"[{r.status_code}] Затраты по объекту #{obj_id}")
        if r.status_code == 200:
            costs = r.json()
            print(f"  -> Данные: {json.dumps(costs, ensure_ascii=False, indent=2)}")
    
    print_section("8. SWAGGER UI")
    print(f"📚 Документация API: http://localhost:8000/docs")
    print(f"📖 ReDoc: http://localhost:8000/redoc")
    
else:
    print("\n❌ Не удалось авторизоваться")
    print("Проверьте данные в БД или создайте пользователя заново")

print("\n" + "="*60)
print("  ✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("="*60 + "\n")
