import pickle
import os
import re
from datetime import datetime, timedelta

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

vendor_transactions = {}
vendor_names = {}

for row in gl_rows:
    if not row:
        continue
    val0 = row[0]
    col0_val = str(val0).strip() if (val0 is not None and val0 == val0) else ""
    
    if col0_val == 'Vendor':
        current_vendor_code = str(row[1]).strip() if (row[1] is not None and row[1] == row[1]) else None
        current_vendor_name = str(row[9]).strip() if (len(row) > 9 and row[9] is not None and row[9] == row[9]) else ""
        if current_vendor_code:
            vendor_names[current_vendor_code] = current_vendor_name
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

def parse_numeric_val(val) -> float:
    if val is None or val != val or val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except:
        return 0.0

out_rows = []
for vcode, txs in vendor_transactions.items():
    last_tx = txs[-1]
    final_bal = parse_numeric_val(last_tx[13])
    
    v_name = vendor_names.get(vcode, "—")
    v_info = po_vendor_info.get(vcode, {})
    country = v_info.get('country', 'India')
    vendor_group = v_info.get('group', 'Domestic vendor')
    
    # 1. Identify all credit/invoice transactions
    credits = []
    for idx, tx in enumerate(txs):
        credit = parse_numeric_val(tx[12])
        if credit > 0:
            credits.append((idx, tx, credit))
            
    # 2. Backward allocation if final_bal < 0
    allocated_map = {}
    if final_bal < 0:
        liability = abs(final_bal)
        allocated = 0.0
        # Walk backwards through credits
        for idx, tx, credit in reversed(credits):
            to_alloc = min(credit, liability - allocated)
            allocated_map[idx] = to_alloc
            allocated += to_alloc
            if allocated >= liability:
                break
                
        # If there is still unallocated liability, create an opening balance row
        if allocated < liability:
            remaining = liability - allocated
            # Add a fake opening balance row
            first_tx = txs[0]
            date_str = str(first_tx[2]).strip() if not (first_tx[2] is None or first_tx[2] != first_tx[2]) else str(first_tx[0]).strip()
            out_rows.append({
                "vendor_code": vcode,
                "vendor_name": v_name,
                "vendor_country": country,
                "vendor_group": vendor_group,
                "invoice_doc_number": "Opening Balance",
                "document_date": date_str,
                "posting_date": date_str,
                "due_date_doc_term": date_str,
                "payment_date": "—",
                "days_late": 0,
                "actual_paid": 0.0,
                "outstanding": remaining,
                "status": "Open",
                "aging_category": "Overdue 0-15"
            })
            
    elif final_bal > 0:
        # Add a fake advance row
        last_tx = txs[-1]
        date_str = str(last_tx[2]).strip() if not (last_tx[2] is None or last_tx[2] != last_tx[2]) else str(last_tx[0]).strip()
        out_rows.append({
            "vendor_code": vcode,
            "vendor_name": v_name,
            "vendor_country": country,
            "vendor_group": vendor_group,
            "invoice_doc_number": "Advance",
            "document_date": date_str,
            "posting_date": date_str,
            "due_date_doc_term": date_str,
            "payment_date": "—",
            "days_late": 0,
            "actual_paid": 0.0,
            "outstanding": final_bal,
            "status": "Open",
            "aging_category": "Overdue 0-15"
        })
        
    # 3. Create rows for all credits
    for idx, tx, credit in credits:
        allocated = allocated_map.get(idx, 0.0)
        outstanding = allocated
        actual_paid = credit - outstanding
        
        # Payment date: search forward for first debit > 0
        payment_date_str = "—"
        for f_tx in txs[idx+1:]:
            f_debit = parse_numeric_val(f_tx[11])
            if f_debit > 0:
                payment_date_str = str(f_tx[2]).strip() if not (f_tx[2] is None or f_tx[2] != f_tx[2]) else str(f_tx[0]).strip()
                break
                
        status = "Fully paid" if outstanding <= 0.01 else ("Open" if actual_paid <= 0.01 else "Partially paid")
        
        doc_date = str(tx[2]).strip() if not (tx[2] is None or tx[2] != tx[2]) else str(tx[0]).strip()
        post_date = str(tx[0]).strip() if not (tx[0] is None or tx[0] != tx[0]) else str(tx[2]).strip()
        due_date = str(tx[1]).strip() if not (tx[1] is None or tx[1] != tx[1]) else doc_date
        
        out_rows.append({
            "vendor_code": vcode,
            "vendor_name": v_name,
            "vendor_country": country,
            "vendor_group": vendor_group,
            "invoice_doc_number": str(tx[5]).strip() if not (tx[5] is None or tx[5] != tx[5]) else "—",
            "document_date": doc_date,
            "posting_date": post_date,
            "due_date_doc_term": due_date,
            "payment_date": payment_date_str,
            "days_late": 0, # we will calculate this in python or let JS consolidator calculate
            "actual_paid": actual_paid,
            "outstanding": outstanding,
            "status": status,
            "aging_category": "Overdue 0-15"
        })

sum_outstanding = sum(r["outstanding"] for r in out_rows if r["status"] in ("Open", "Partially paid"))
print(f"Total open invoice rows: {len(out_rows)}")
print(f"Total outstanding sum: {sum_outstanding:.2f} INR = {sum_outstanding/1e7:.2f} Cr")
