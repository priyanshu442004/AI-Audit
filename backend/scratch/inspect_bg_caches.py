import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
files = [
    "aging_domestic.pkl",
    "aging_foreign.pkl",
    "aging_related.pkl",
    "aging_msme.pkl",
    "vendor_master_new.pkl",
    "three_way_matching.pkl",
    "price_variance_same.pkl",
    "price_variance_cross.pkl"
]

for fn in files:
    p = os.path.join(cache_dir, fn)
    if os.path.exists(p):
        try:
            with open(p, "rb") as f:
                data = pickle.load(f)
            print(f"File {fn}:")
            print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            if isinstance(data, dict):
                print(f"  KPIs: {data.get('kpis', {})}")
                rows = data.get("rows", [])
                print(f"  Rows count: {len(rows)}")
                if len(rows) > 0:
                    print(f"  Sample row keys: {list(rows[0].keys())}")
        except Exception as e:
            print(f"Error reading {fn}: {e}")
    else:
        print(f"File {fn} does not exist!")
