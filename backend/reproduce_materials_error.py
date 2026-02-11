import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
REQUESTS_URL = f"{BASE_URL}/material-requests/"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    try:
        response = requests.post(
            LOGIN_URL,
            json={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Failed to login: {e}")
        if response.status_code != 200:
             print(f"Response: {response.text}")
        sys.exit(1)

def test_create_request(token, payload, description):
    print(f"\n--- Testing {description} ---")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(REQUESTS_URL, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code in [200, 201]:
            print("Success!")
            print(f"Response: {response.text[:200]}...")
        else:
            print("Failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Exception calling endpoint: {e}")

def main():
    print("Starting reproduction script for Material Requests...")
    token = get_token()
    print("Logged in successfully.")

    # 1. Valid Payload
    valid_payload = {
        "cost_object_id": 8, # Using known object ID
        "material_type": "regular",
        "urgency": "normal",
        "items": [
            {
                "material_name": "Test Material",
                "quantity": 10,
                "unit": "kg",
                "description": "Test description"
            }
        ],
        "comment": "Test request"
    }
    test_create_request(token, valid_payload, "Valid Payload")

    # 2. Invalid Payload (Empty items)
    invalid_payload_1 = {
        "cost_object_id": 8,
        "material_type": "regular",
        "urgency": "normal",
        "items": [], # Empty list - should fail min_items=1
        "comment": "Empty items"
    }
    test_create_request(token, invalid_payload_1, "Invalid Payload (Empty Items)")

    # 3. Invalid Payload (Missing required field urgency)
    invalid_payload_2 = {
        "cost_object_id": 8,
        "material_type": "regular",
        "items": [
             {
                "material_name": "Test Material",
                "quantity": 10,
                "unit": "kg"
            }
        ]
    }
    test_create_request(token, invalid_payload_2, "Invalid Payload (Missing Urgency)")

if __name__ == "__main__":
    main()
