import pickle
import os
import pandas as pd

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def analyze_overdue(fname):
    path = os.path.join(cache_dir, fname)
    if not os.path.exists(path):
        return 0, 0, 0
    with open(path, "rb") as f:
        data = pickle.load(f)
    rows = data.get("rows", [])
    
    # 1. Calculate final balance per vendor
    vendor_balances = {}
    for r in rows:
        vcode = r.get("vendor_code")
        if vcode:
            vendor_balances[vcode] = abs(float(r.get("outstanding") or 0.0))
            
    # Find max date
    dates = []
    for r in rows:
        d_str = r.get("posting_date") or r.get("document_date")
        if d_str and d_str != '—':
            try:
                dates.append(pd.to_datetime(d_str, format="%d/%m/%y"))
            except:
                try:
                    dates.append(pd.to_datetime(d_str))
                except:
                    pass
    max_date = max(dates) if dates else None
    
    # 2. Count overdue transactions and unique docs
    overdue_rows_total_bal = 0
    overdue_rows_active_vendor = 0
    overdue_docs_active_vendor = set()
    
    for r in rows:
        vcode = r.get("vendor_code")
        if not vcode:
            continue
        
        status = r.get("status")
        is_open = status in ('Open', 'Partially paid')
        due_str = r.get("due_date_doc_term") or r.get("due_date")
        
        if is_open and due_str and due_str != '—' and max_date:
            try:
                due_dt = pd.to_datetime(due_str, format="%d/%m/%y")
            except:
                try:
                    due_dt = pd.to_datetime(due_str)
                except:
                    due_dt = None
            
            if due_dt and due_dt < max_date:
                overdue_rows_total_bal += 1
                if vendor_balances.get(vcode, 0.0) > 1.0: # Vendor has active outstanding balance > 1 Rupee
                    overdue_rows_active_vendor += 1
                    doc_no = r.get("invoice_doc_number")
                    if doc_no and doc_no != '—':
                        overdue_docs_active_vendor.add(doc_no)
                        
    return overdue_rows_total_bal, overdue_rows_active_vendor, len(overdue_docs_active_vendor)

for fname in ["aging_domestic.pkl", "aging_foreign.pkl", "aging_related.pkl", "aging_msme.pkl"]:
    r_all, r_act, docs_act = analyze_overdue(fname)
    print(f"{fname}:")
    print(f"  All overdue rows: {r_all}")
    print(f"  Overdue rows for active vendors: {r_act}")
    print(f"  Overdue unique docs for active vendors: {docs_act}")
