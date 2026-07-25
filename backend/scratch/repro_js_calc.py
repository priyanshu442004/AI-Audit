import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def repro_js(file_name):
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
        if amt > 0 and status in ("Open", "Partially paid"):
            total += amt
            count += 1
    print(f"{file_name}: total={total:.2f}, count={count}")
    return total

t1 = repro_js("aging_domestic.pkl")
t2 = repro_js("aging_foreign.pkl")
print(f"Total Cr: {(t1+t2)/1e7:.2f}")
