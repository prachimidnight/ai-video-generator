import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_user_lifecycle():
    # 1. Create a test user
    print("--- Testing User Lifecycle ---")
    signup_data = {
        "full_name": "Test User",
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/signup", json=signup_data)
    if response.status_code != 200:
        print(f"FAILED: Signup failed with {response.status_code}")
        print(response.text)
        return
    
    user = response.json()
    user_id = user.get("id")
    if not user_id:
        # Try to get id from /admin/users if not in signup response
        users_resp = requests.get(f"{BASE_URL}/admin/users")
        for u in users_resp.json().get("data", []):
            if u["email"] == signup_data["email"]:
                user_id = u["id"]
                break
    
    print(f"User created with ID: {user_id}")

    # 2. Update the user
    update_data = {
        "full_name": "Updated Test User",
        "subscription_tier": "pro",
        "available_credits": 100,
        "status": False
    }
    
    print(f"Updating user {user_id}...")
    update_resp = requests.put(f"{BASE_URL}/admin/users/{user_id}", json=update_data)
    if update_resp.status_code == 200:
        print("SUCCESS: User updated successfully")
        print(json.dumps(update_resp.json(), indent=2))
    else:
        print(f"FAILED: User update failed with {update_resp.status_code}")
        print(update_resp.text)

    # 3. Delete the user
    print(f"Deleting user {user_id}...")
    delete_resp = requests.delete(f"{BASE_URL}/admin/users/{user_id}")
    if delete_resp.status_code == 200:
        print("SUCCESS: User deleted successfully")
    else:
        print(f"FAILED: User deletion failed with {delete_resp.status_code}")
        print(delete_resp.text)

if __name__ == "__main__":
    try:
        test_user_lifecycle()
    except Exception as e:
        print(f"An error occurred: {e}")
