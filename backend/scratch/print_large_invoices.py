import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

invoice_lasts = {}
for r in rows:
    vcode = r.get("vendor_code")
    inv_no = r.get("invoice_doc_number")
    if vcode and inv_no and inv_no != "—":
        key = (vcode, inv_no)
        invoice_lasts[key] = r

sorted_invoices = sorted(
    [(key, r) for key, r in invoice_lasts.items() if r.get("status") in ("Open", "Partially paid")],
    key=lambda x: abs(float(x[1].get("outstanding") or 0.0)),
    reverse=True
)

print("Top 10 outstanding invoices:")
for key, r in sorted_invoices[:10]:
    print(f"Key: {key}, Out: {r.get('outstanding')}, Status: {r.get('status')}, Vendor Name: {r.get('vendor_name')}")
