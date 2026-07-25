import pickle
import os
from collections import Counter

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

for fname in ["aging_domestic.pkl", "aging_msme.pkl"]:
    with open(os.path.join(cache_dir, fname), "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    statuses = Counter(r.get("status") for r in rows)
    outstanding_signs = Counter("pos" if float(r.get("outstanding") or 0.0) > 0 else "neg_or_zero" for r in rows)
    
    print(f"File: {fname}")
    print(f"  Statuses: {dict(statuses)}")
    print(f"  Outstanding signs: {dict(outstanding_signs)}")
