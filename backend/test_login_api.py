import requests
import sys

API_URL = "http://localhost:8000/api/v1/auth/login"

def test_login_api():
    print(f"Testing Login API: {API_URL}")
    
    # 1. Test with wrong password
    print("\n1. Testing with WRONG password...")
    try:
        response = requests.post(API_URL, json={
            "username": "admin",
            "password": "wrong_password_123"
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 500:
            print("🚨 REPRODUCED 500 ERROR with wrong password!")
        elif response.status_code == 401:
            print("✅ Correctly returned 401 for wrong password")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"Request failed: {e}")

    # 2. Test with empty body (validation error expected 422)
    print("\n2. Testing with empty body...")
    try:
        response = requests.post(API_URL, json={})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

    # 3. Test with CORRECT password
    print("\n3. Testing with CORRECT password...")
    try:
        response = requests.post(API_URL, json={
            "username": "admin",
            "password": "admin123"
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...") # Truncate token
        
        if response.status_code == 500:
            print("🚨 REPRODUCED 500 ERROR on successful login!")
        elif response.status_code == 200:
            print("✅ Login SUCCESSFUL")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_login_api()
