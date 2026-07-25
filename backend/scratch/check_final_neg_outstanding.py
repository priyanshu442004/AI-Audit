import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def check_final_outstanding(file_name):
    p = os.path.join(cache_dir, file_name)
    if not os.path.exists(p):
        return 0.0
    with open(p, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    vendor_lasts = {}
    for r in rows:
        vcode = r.get("vendor_code")
        if vcode:
            vendor_lasts[vcode] = r
            
    total = 0.0
    for r in vendor_lasts.values():
        o = float(r.get("outstanding") or 0.0)
        if o < 0:
            total += abs(o)
    print(f"{file_name}: final negative balance sum={total:.2f} = {total/1e7:.2f} Cr, count={len(vendor_lasts)}")
    return total

check_final_outstanding("aging_msme.pkl")
check_final_outstanding("aging_related.pkl")
