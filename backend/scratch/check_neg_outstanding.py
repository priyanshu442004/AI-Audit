import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def check_negative_outstanding(file_name):
    p = os.path.join(cache_dir, file_name)
    if not os.path.exists(p):
        return 0.0
    with open(p, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    total = 0.0
    count = 0
    for r in rows:
        amt = float(r.get("outstanding") or 0.0)
        status = r.get("status")
        if amt < 0 and status in ("Open", "Partially paid"):
            total += abs(amt)
            count += 1
    print(f"{file_name}: negative outstanding sum={total:.2f}, count={count}")
    return total

t1 = check_negative_outstanding("aging_domestic.pkl")
t2 = check_negative_outstanding("aging_foreign.pkl")
t3 = check_negative_outstanding("aging_related.pkl")
t4 = check_negative_outstanding("aging_msme.pkl")
print(f"Total Cr: {(t1+t2+t3+t4)/1e7:.2f}")
