import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

# Find rows with prefix SO or SI
so_rows = [r for r in rows if r.get("invoice_doc_number", "").startswith("SO") or r.get("invoice_doc_number", "").startswith("SI")]
print(f"Total SO/SI rows: {len(so_rows)}")
if so_rows:
    for i in range(min(5, len(so_rows))):
        r = so_rows[i]
        print(f"Vendor: {r.get('vendor_code')}, Name: {r.get('vendor_name')}, Doc: {r.get('invoice_doc_number')}, Out: {r.get('outstanding')}")
