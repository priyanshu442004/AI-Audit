import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_msme.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])
for i in range(min(5, len(rows))):
    print(rows[i])
