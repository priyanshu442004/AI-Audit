import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])
negative_count = 0
positive_count = 0
zero_count = 0
for r in rows:
    o = float(r.get("outstanding") or 0.0)
    if o < 0:
        negative_count += 1
    elif o > 0:
        positive_count += 1
    else:
        zero_count += 1
print(f"Domestic aging: negative={negative_count}, positive={positive_count}, zero={zero_count}")
