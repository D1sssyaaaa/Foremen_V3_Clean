import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login"
USERNAME = "admin"
PASSWORD = "admin123"

def get_token():
    try:
        response = requests.post(
            LOGIN_URL,
            json={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {response.text}")
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Failed to login: {e}")
        sys.exit(1)

def test_endpoint(token, url_suffix, description):
    print(f"\n--- Testing {description} ---")
    url = f"{BASE_URL}{url_suffix}"
    print(f"GET {url}")
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
        else:
            print("Success!")
            # Print first 200 chars to verify content
            print(f"Content preview: {response.text[:200]}...")
    except Exception as e:
        print(f"Exception calling endpoint: {e}")

def main():
    print("Starting reproduction script...")
    token = get_token()
    print("Logged in successfully.")

    # Test Case 1: Object Costs (User reported 500 on ID 8)
    # First, let's list objects to see if ID 8 exists, or pick a valid one
    print("\nListing objects to verify ID...")
    objects_url = f"{BASE_URL}/objects/"
    try:
        resp = requests.get(objects_url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            objects = resp.json()
            if objects:
                # print first few IDs
                print(f"Found {len(objects)} objects. IDs: {[o['id'] for o in objects[:5]]}")
                target_id = 8
                # Check if 8 is in list
                if not any(o['id'] == target_id for o in objects):
                    print(f"Object ID {target_id} not found in list. Using first available ID if possible.")
                    if objects:
                        target_id = objects[0]['id']
                
                test_endpoint(token, f"/objects/{target_id}/costs", f"Object Costs (ID {target_id})")
            else:
                print("No objects found in DB.")
        else:
            print(f"Failed to list objects: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error listing objects: {e}")

    # Test Case 2: UPD Suggestions (User reported 500 on ID 110)
    print("\nListing UPDs to verify ID...")
    upd_url = f"{BASE_URL}/material-costs/" # Endpoint is /material-costs/ based on prefix
    try:
        resp = requests.get(upd_url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            upds = resp.json()
            if upds:
                 # print first few IDs
                print(f"Found {len(upds)} UPDs. IDs: {[u['id'] for u in upds[:5]]}")
                target_upd_id = 110
                if not any(u['id'] == target_upd_id for u in upds):
                    print(f"UPD ID {target_upd_id} not found. Using first available ID.")
                    if upds:
                        target_upd_id = upds[0]['id']
                
                test_endpoint(token, f"/material-costs/{target_upd_id}/suggestions", f"UPD Suggestions (ID {target_upd_id})")
            else:
                print("No UPDs found in DB.")
        else:
            print(f"Failed to list UPDs: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error listing UPDs: {e}")

if __name__ == "__main__":
    main()
