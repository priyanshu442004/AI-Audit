import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

for fname in ["aging_domestic.pkl", "aging_foreign.pkl", "aging_related.pkl", "aging_msme.pkl"]:
    path = os.path.join(cache_dir, fname)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        rows = data.get("rows", [])
        
        sum_pos = 0.0
        sum_neg = 0.0
        open_pos_sum = 0.0
        open_neg_sum = 0.0
        
        for r in rows:
            val = float(r.get("outstanding") or 0.0)
            status = r.get("status")
            isOpen = status in ('Open', 'Partially paid')
            if val > 0:
                sum_pos += val
                if isOpen:
                    open_pos_sum += val
            else:
                sum_neg += val
                if isOpen:
                    open_neg_sum += val
        
        print(f"{fname}:")
        print(f"  Positive sum: {sum_pos}, Open positive sum: {open_pos_sum}")
        print(f"  Negative sum: {sum_neg}, Open negative sum: {open_neg_sum}")
