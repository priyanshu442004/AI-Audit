import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def test_invoice_aggregation(file_name):
    p = os.path.join(cache_dir, file_name)
    if not os.path.exists(p):
        return
    with open(p, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    # 1. Group by (vendor_code, invoice_doc_number) and take the last row
    invoice_lasts = {}
    for r in rows:
        vcode = r.get("vendor_code")
        inv_no = r.get("invoice_doc_number")
        if vcode and inv_no and inv_no != "—":
            key = (vcode, inv_no)
            invoice_lasts[key] = r
            
    # Calculate sum of outstanding balances for open/partially paid invoices
    sum_outstanding = 0.0
    open_count = 0
    for key, r in invoice_lasts.items():
        status = r.get("status")
        if status in ("Open", "Partially paid"):
            o = float(r.get("outstanding") or 0.0)
            sum_outstanding += abs(o)
            open_count += 1
            
    print(f"\nInvoice-level aggregation for {file_name}:")
    print(f"  Total unique invoices: {len(invoice_lasts)}")
    print(f"  Open/Partially paid invoices: {open_count}")
    print(f"  Sum of absolute outstanding: {sum_outstanding:.2f} INR = {sum_outstanding/1e7:.2f} Cr")

test_invoice_aggregation("aging_domestic.pkl")
test_invoice_aggregation("aging_foreign.pkl")
test_invoice_aggregation("aging_related.pkl")
test_invoice_aggregation("aging_msme.pkl")
