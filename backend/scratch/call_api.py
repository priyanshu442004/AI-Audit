import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

try:
    r = requests.get(f"{backend_url}/api/analysis/price-variance-same")
    print("Status Code:", r.status_code)
    print("Response JSON:")
    try:
        print(r.json())
    except:
        print(r.text)
except Exception as e:
    print("Connection failed:", e)
