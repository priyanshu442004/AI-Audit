import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/result/combined"
res = requests.get(url)
data = res.json()
po_missing = data.get("postatus", {}).get("po_missing", {})

for key, sheet_data in po_missing.items():
    print(f"\n================ SHEET: {key} ({sheet_data.get('title')}) ================")
    print("  KPIS    :", sheet_data.get("kpis"))
    print("  COLUMNS :", sheet_data.get("columns"))
    rows = sheet_data.get("rows", [])
    print(f"  ROW COUNT: {len(rows)}")
    if rows:
        print("  ROW 1 KEYS:", list(rows[0].keys()))
