"""Тестирование проблемных endpoints"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

# Логин
login_resp = requests.post(
    f"{API_BASE}/auth/login",
    json={"username": "admin", "password": "admin123"}
)
print(f"Login: {login_resp.status_code}")
token = login_resp.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Тестируем material-requests
print("\n--- Testing /material-requests/ ---")
try:
    resp = requests.get(f"{API_BASE}/material-requests/", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.ok:
        print(f"Response: {resp.json()}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

# Тестируем equipment-orders
print("\n--- Testing /equipment-orders/ ---")
try:
    resp = requests.get(f"{API_BASE}/equipment-orders/", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.ok:
        print(f"Response: {resp.json()}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

# Тестируем time-sheets
print("\n--- Testing /time-sheets/ ---")
try:
    resp = requests.get(f"{API_BASE}/time-sheets/", headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.ok:
        print(f"Response: {resp.json()}")
    else:
        print(f"Error: {resp.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
