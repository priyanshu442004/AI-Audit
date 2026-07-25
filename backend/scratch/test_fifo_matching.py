import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

# Mock the vendor mappings
po_path = os.path.join(cache_dir, "7145fca09fa8c896029d0326324dba61.pkl")
with open(po_path, "rb") as f:
    df_po = pickle.load(f)
po_vendor_info = {}
for idx, row in df_po.iterrows():
    vcode = str(row.get("Vendor Code", "")).strip()
    if vcode:
        curr = str(row.get("Document Currency", "")).strip()
        vgroup = str(row.get("Vendor Group", "")).strip()
        country = "India" if curr.upper() in ("INR", "") else "USA"
        po_vendor_info[vcode] = {'country': country, 'group': vgroup}

gl_rows = df_gl.values.tolist()
current_vendor_code = None
current_vendor_name = None

non_vendor_cats = {'Revenue', 'Asset', 'Equity', 'Expenditure', 'Liability', 'Customer'}

# Group transactions by vendor
vendor_transactions = {}

for row in gl_rows:
    if not row:
        continue
    val0 = row[0]
    col0_val = str(val0).strip() if (val0 is not None and val0 == val0) else ""
    
    if col0_val == 'Vendor':
        current_vendor_code = str(row[1]).strip() if (row[1] is not None and row[1] == row[1]) else None
        current_vendor_name = str(row[9]).strip() if (len(row) > 9 and row[9] is not None and row[9] == row[9]) else ""
    elif col0_val in non_vendor_cats:
        current_vendor_code = None
        current_vendor_name = None
        
    if not current_vendor_code:
        continue
        
    # Process transactional row
    if not col0_val or col0_val.lower() in ("nan", "none", "vendor"):
        continue
        
    v_info = po_vendor_info.get(current_vendor_code, {})
    country = v_info.get('country', 'India')
    if country != 'India':
        continue
        
    if current_vendor_code not in vendor_transactions:
        vendor_transactions[current_vendor_code] = []
    vendor_transactions[current_vendor_code].append(row)

# Now apply FIFO matching for each vendor
total_outstanding = 0.0
open_invoices_count = 0

for vcode, txs in vendor_transactions.items():
    invoices = [] # list of {"doc_no": ..., "amount": ..., "remaining": ...}
    payments = [] # list of values
    
    for tx in txs:
        # col 5 is DocNo, col 11 is Debit, col 12 is Credit
        doc_no = str(tx[5]).strip() if len(tx) > 5 else ""
        debit = float(str(tx[11]).replace(",", "").strip()) if (len(tx) > 11 and tx[11] is not None and str(tx[11]).strip() != "") else 0.0
        credit = float(str(tx[12]).replace(",", "").strip()) if (len(tx) > 12 and tx[12] is not None and str(tx[12]).strip() != "") else 0.0
        
        if credit > 0:
            invoices.append({
                "doc_no": doc_no,
                "amount": credit,
                "remaining": credit
            })
        if debit > 0:
            payments.append(debit)
            
    # Apply payments to invoices FIFO
    for pay_amt in payments:
        for inv in invoices:
            if inv["remaining"] > 0:
                allocated = min(pay_amt, inv["remaining"])
                inv["remaining"] -= allocated
                pay_amt -= allocated
                if pay_amt <= 0:
                    break
                    
    # Check remaining outstanding
    v_out = sum(inv["remaining"] for inv in invoices if inv["remaining"] > 0)
    total_outstanding += v_out
    open_invoices_count += sum(1 for inv in invoices if inv["remaining"] > 0)

print(f"FIFO total outstanding: {total_outstanding:.2f} INR = {total_outstanding/1e7:.2f} Cr")
print(f"FIFO total open invoices count: {open_invoices_count}")
