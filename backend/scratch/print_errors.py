import pickle
import os

cache_path = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs\pipeline_result.pkl"
if os.path.exists(cache_path):
    with open(cache_path, "rb") as f:
        res = pickle.load(f)
    for k, v in res.items():
        if isinstance(v, dict) and "error" in v:
            print(f"Section {k} failed with error: {v['error']}")
else:
    print("pipeline_result.pkl not found!")
