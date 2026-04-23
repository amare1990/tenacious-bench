import os
import requests

from dotenv import load_dotenv
load_dotenv()

token = os.getenv("HUBSPOT_API_KEY")
print("token starts with:", token[:8] if token else None)

url = "https://api.hubapi.com/crm/v3/objects/contacts"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
data = {
    "properties": {
        "email": "test@example.com",
        "firstname": "Test",
        "lastname": "Lead",
    }
}

res = requests.post(url, json=data, headers=headers, timeout=30)
print(res.status_code)
print(res.text)
