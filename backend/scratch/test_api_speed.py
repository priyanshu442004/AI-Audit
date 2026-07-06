import time
import urllib.request
import json
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

url = f"{backend_url}/api/analysis/payment-aging-domestic"

print(f"Sending GET request to {url}...")
t0 = time.time()
try:
    with urllib.request.urlopen(url) as response:
        status = response.getcode()
        headers = response.info()
        data = response.read()
        t1 = time.time()
        print(f"Success! Status: {status}")
        print(f"Response Size: {len(data) / (1024*1024):.2f} MB")
        print(f"Total Time Taken: {t1 - t0:.2f} seconds")
        
        # Parse some JSON to check validity
        parsed = json.loads(data.decode('utf-8'))
        print(f"Number of rows parsed from JSON: {len(parsed.get('rows', []))}")
except Exception as e:
    t1 = time.time()
    print(f"Request failed: {e}")
    print(f"Time elapsed: {t1 - t0:.2f} seconds")
