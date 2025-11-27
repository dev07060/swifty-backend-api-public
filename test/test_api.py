import requests
import json
import uuid
from datetime import datetime

# Base URL of the API
BASE_URL = "http://127.0.0.1:8000"

# Generate a unique user key for this test run
USER_KEY = '9af9778d-cf8f-4ebd-807c-f6d4873b5fcc'
    # str(uuid.uuid4()))

# def test_create_user():
#     """Tests the user creation endpoint."""
#     url = f"{BASE_URL}/api/users"
#     payload = {
#         "userKey": USER_KEY,
#         "gender": "female",
#         "ageRange": "25-34"
#     }
#     headers = {"Content-Type": "application/json"}
#
#     print(f"--- Testing POST {url} ---")
#     try:
#         response = requests.post(url, data=json.dumps(payload), headers=headers)
#         print(f"Status Code: {response.status_code}")
#         print("Response JSON:", response.json())
#         response.raise_for_status()
#         return True
#     except requests.exceptions.RequestException as e:
#         print(f"Error: {e}")
#         return False

def test_log_exercise():
    """Tests the exercise logging endpoint."""
    url = f"{BASE_URL}/api/log/exercise"
    payload = {
        "userKey": USER_KEY,
        "exerciseType": "Weightlifting",
        "duration": 60,
        # "calories": 400,
        "date": datetime.now().strftime("%Y-%m-%d"),
        # "distance": 0
    }
    headers = {"Content-Type": "application/json"}

    print(f"\n--- Testing POST {url} ---")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:", response.json())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def test_log_food():
    """
    Tests the food logging endpoint.
    NOTE: This test will fail if the ingredients listed below do not exist
    in your 'ingredients' master table. You may need to add them manually
    to your database before running this test.
    e.g., INSERT INTO swifty_app.ingredients (name) VALUES ('Salmon'), ('Asparagus'), ('Sweet Potato');
    """
    url = f"{BASE_URL}/api/log/food"
    payload = {
        "userKey": USER_KEY,
        "isHealthy": True,
        "mainIngredients": ["Salmon", "Asparagus", "Sweet Potato"],
        "estimatedCalories": 550,
        "mealType": "Dinner",
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    headers = {"Content-Type": "application/json"}

    print(f"\n--- Testing POST {url} ---")
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:", response.json())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_get_user_logs():
    """Tests retrieving user logs."""
    url = f"{BASE_URL}/api/log/exercise/today"
    params = {"userKey": USER_KEY}
    headers = {"Content-Type": "application/json"}

    print(f"\n--- Testing GET {url} with userKey={USER_KEY} ---")
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:", response.json())
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Starting API tests...")
    
    # First, create a user
    # if test_create_user():
        # If user creation is successful, test the other endpoints
    test_log_exercise()
    test_log_food()
    test_get_user_logs()
    # else:
    #     print("\nUser creation failed. Aborting other tests.")
        
    print("\nAPI tests finished.")
