import requests

try:
    r = requests.get("http://127.0.0.1:8000/api/analysis/price-variance-same")
    print("Status Code:", r.status_code)
    print("Response JSON:")
    try:
        print(r.json())
    except:
        print(r.text)
except Exception as e:
    print("Connection failed:", e)
