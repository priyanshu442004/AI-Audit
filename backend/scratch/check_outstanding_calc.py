import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def check_outstanding(file_name):
    p = os.path.join(cache_dir, file_name)
    if not os.path.exists(p):
        print(f"{file_name} does not exist!")
        return 0.0
    with open(p, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    # Group by vendor and find the last row (since they are sorted by vendor and date)
    vendor_lasts = {}
    for r in rows:
        vcode = r.get("vendor_code")
        if vcode:
            vendor_lasts[vcode] = r
            
    # Sum the outstanding of the last row for each vendor
    total_outstanding = 0.0
    for vcode, r in vendor_lasts.items():
        o = float(r.get("outstanding") or 0.0)
        # In vendor ledger, credit balance is negative (meaning we owe money).
        # We only want to sum vendor credit balances (outstanding payables).
        # If the vendor has a debit balance (positive outstanding), it means overpayment/advance, which is an asset, not a liability.
        # But let's check both ways.
        if o < 0:
            total_outstanding += abs(o)
            
    print(f"File {file_name}:")
    print(f"  Unique vendors: {len(vendor_lasts)}")
    print(f"  Total trade payables (sum of negative balances): {total_outstanding:.2f} (INR) = {total_outstanding / 1e7:.2f} Cr")
    
    # What if we sum all positive and negative (net)?
    net_outstanding = sum(float(r.get("outstanding") or 0.0) for r in vendor_lasts.values())
    print(f"  Net outstanding (net of advances): {-net_outstanding:.2f} (INR) = {-net_outstanding / 1e7:.2f} Cr")
    return total_outstanding

dom = check_outstanding("aging_domestic.pkl")
forg = check_outstanding("aging_foreign.pkl")
print(f"Consolidated Outstanding Payables (Domestic + Foreign): {(dom + forg) / 1e7:.2f} Cr")
