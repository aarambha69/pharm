
import requests
import json

API_BASE = "http://localhost:5000/api"

def debug_clients():
    # Login
    print("Logging in...")
    try:
        # Try the hardcoded fallback
        res = requests.post(f"{API_BASE}/login", json={
            "phone": "9855062769",
            "password": "123" # Incorrect password to trigger fallback check or real DB check
        })
        
        # If that fails, try the other known password
        if res.status_code != 200:
             res = requests.post(f"{API_BASE}/login", json={
                "phone": "9855062769",
                "password": "987654321" 
            })
             
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return

        token = res.json().get('token')
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get Clients
        print("Fetching clients...")
        res = requests.get(f"{API_BASE}/super/clients", headers=headers)
        if res.status_code == 200:
            data = res.json()
            print(f"Found {len(data)} clients.")
            print(json.dumps(data, indent=2))
        else:
            print(f"Failed to fetch clients: {res.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_clients()
