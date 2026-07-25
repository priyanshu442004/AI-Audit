import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

for fname in os.listdir(cache_dir):
    if fname.endswith(".pkl"):
        try:
            with open(os.path.join(cache_dir, fname), "rb") as f:
                data = pickle.load(f)
            
            print(f"File: {fname}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
                if "rows" in data:
                    print(f"  Number of rows: {len(data['rows'])}")
                    if data["rows"]:
                        print(f"  First row sample: {data['rows'][0]}")
                if "kpis" in data:
                    print(f"  KPIs: {data['kpis']}")
            else:
                print(f"  Type: {type(data)}")
        except Exception as e:
            print(f"Error reading {fname}: {e}")
