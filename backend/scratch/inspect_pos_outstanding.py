import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)

rows = data.get("rows", [])
pos_rows = [r for r in rows if float(r.get("outstanding") or 0.0) > 1e6]
print("Number of positive outstanding rows > 10L:", len(pos_rows))
if pos_rows:
    for r in pos_rows[:10]:
        print(r)
