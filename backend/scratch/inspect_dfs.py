import pickle
import pandas as pd
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def inspect_file(name):
    path = os.path.join(cache_dir, name)
    if not os.path.exists(path):
        print(f"{name} does not exist")
        return
    with open(path, "rb") as f:
        data = pickle.load(f)
    print(f"\n=== INSPECTING {name} ===")
    print("Type of data:", type(data))
    if isinstance(data, dict):
        print("Keys:", list(data.keys()))
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  Key '{k}': list of length {len(v)}")
                if len(v) > 0:
                    print("  First element type:", type(v[0]))
                    print("  First element:", v[0])
            elif isinstance(v, dict):
                print(f"  Key '{k}': dict with keys {list(v.keys())}")
            else:
                print(f"  Key '{k}': {type(v)}")
    elif isinstance(data, pd.DataFrame):
        print("Shape:", data.shape)
        print("Columns:", list(data.columns))
        print("Head:")
        print(data.head(2))

inspect_file("three_way_matching.pkl")
inspect_file("price_variance_same.pkl")
inspect_file("price_variance_cross.pkl")
inspect_file("aging_domestic.pkl")
