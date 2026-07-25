import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def test_invoice_grouping(file_name):
    p = os.path.join(cache_dir, file_name)
    if not os.path.exists(p):
        return
    with open(p, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    # Let's inspect a few vendors' invoices
    # For each invoice (vendor_code + invoice_doc_number), let's track the rows
    invoice_rows = {}
    for r in rows:
        vcode = r.get("vendor_code")
        inv_no = r.get("invoice_doc_number")
        if vcode and inv_no and inv_no != "—":
            key = (vcode, inv_no)
            if key not in invoice_rows:
                invoice_rows[key] = []
            invoice_rows[key].append(r)
            
    print(f"\nFile: {file_name}")
    print(f"Total unique invoices: {len(invoice_rows)}")
    
    # Print 5 invoices with multiple rows
    count = 0
    for key, r_list in invoice_rows.items():
        if len(r_list) > 1:
            print(f"Invoice {key}: {len(r_list)} transactions")
            for r in r_list:
                print(f"  Date: {r.get('posting_date')}, Status: {r.get('status')}, Outstanding: {r.get('outstanding')}, Paid: {r.get('actual_paid')}")
            count += 1
            if count >= 3:
                break
                
test_invoice_grouping("aging_domestic.pkl")
