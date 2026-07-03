import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

try:
    res = requests.get(f"{backend_url}/api/analysis/price-variance-same")
    print(f"Status: {res.status_code}")
    data = res.json()
    if isinstance(data, dict):
        print("Keys in response:", list(data.keys()))
        rows = data.get("rows", [])
        print(f"Number of rows: {len(rows)}")
        if rows:
            print("First row keys:", list(rows[0].keys()))
            print("First row sample:", rows[0])
    else:
        print("Response is not a dict:", type(data))
except Exception as e:
    print("Error calling endpoint:", e)
