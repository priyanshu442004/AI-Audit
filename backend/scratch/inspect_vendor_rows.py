import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

# Find a vendor with some rows
vendor_rows = {}
for r in rows:
    vcode = r.get("vendor_code")
    if vcode not in vendor_rows:
        vendor_rows[vcode] = []
    vendor_rows[vcode].append(r)

# Print first 2 vendors' last 5 rows
for vcode in list(vendor_rows.keys())[:3]:
    v_rows = vendor_rows[vcode]
    print(f"Vendor: {vcode}, Name: {v_rows[0].get('vendor_name')}, Total rows: {len(v_rows)}")
    for r in v_rows[-5:]:
        print(f"  DocNo: {r.get('invoice_doc_number')}, Date: {r.get('posting_date')}, Status: {r.get('status')}, Outstanding: {r.get('outstanding')}, Paid: {r.get('actual_paid')}")
