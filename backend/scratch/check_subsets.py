import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def get_vendors(fname):
    path = os.path.join(cache_dir, fname)
    if not os.path.exists(path):
        return set()
    with open(path, "rb") as f:
        data = pickle.load(f)
    return {r.get("vendor_code") for r in data.get("rows", []) if r.get("vendor_code")}

domestic = get_vendors("aging_domestic.pkl")
foreign = get_vendors("aging_foreign.pkl")
related = get_vendors("aging_related.pkl")
msme = get_vendors("aging_msme.pkl")

print(f"Domestic unique vendors: {len(domestic)}")
print(f"Foreign unique vendors: {len(foreign)}")
print(f"Related unique vendors: {len(related)}")
print(f"MSME unique vendors: {len(msme)}")

print(f"Related in Domestic: {len(related.intersection(domestic))} / {len(related)}")
print(f"MSME in Domestic: {len(msme.intersection(domestic))} / {len(msme)}")
print(f"Foreign in Domestic: {len(foreign.intersection(domestic))}")

# Let's calculate the final outstanding balance for Domestic and Foreign using the fast method
# Since rows are sorted by vendor_code and posting_date, the last row for each vendor code in the list has the final balance
def get_final_balances(fname):
    path = os.path.join(cache_dir, fname)
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        data = pickle.load(f)
    
    balances = {}
    for r in data.get("rows", []):
        vcode = r.get("vendor_code")
        if vcode:
            balances[vcode] = abs(float(r.get("outstanding") or 0.0))
    return balances

dom_bal = get_final_balances("aging_domestic.pkl")
for_bal = get_final_balances("aging_foreign.pkl")

print(f"Domestic Outstanding Sum: {sum(dom_bal.values()):.2f} (in Cr: {sum(dom_bal.values())/1e7:.2f})")
print(f"Foreign Outstanding Sum: {sum(for_bal.values()):.2f} (in Cr: {sum(for_bal.values())/1e7:.2f})")
print(f"Total Combined Outstanding: {(sum(dom_bal.values()) + sum(for_bal.values())):.2f} (in Cr: {(sum(dom_bal.values()) + sum(for_bal.values()))/1e7:.2f})")
