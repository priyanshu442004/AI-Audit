import pickle
import os
from datetime import datetime

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def fast_parse_date(date_str):
    if not date_str or date_str in ('—', '', ''):
        return None
    date_str = str(date_str).strip()
    # Try dd/mm/yy or dd/mm/yyyy
    parts = date_str.split('/')
    if len(parts) == 3:
        try:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            if year < 100:
                year += 2000
            return datetime(year, month, day)
        except:
            pass
    # Try yyyy-mm-dd
    parts = date_str.split('-')
    if len(parts) == 3:
        try:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            return datetime(year, month, day)
        except:
            pass
    return None

with open(os.path.join(cache_dir, "aging_msme.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

# Find max date
max_date = None
for r in rows:
    d_str = r.get("posting_date") or r.get("document_date")
    dt = fast_parse_date(d_str)
    if dt:
        if max_date is None or dt > max_date:
            max_date = dt

if max_date is None:
    max_date = datetime(2026, 3, 31)

print("Max Date:", max_date)

# Group rows by invoice_doc_number + vendor_code
invoices = {}
for r in rows:
    doc_no = r.get("invoice_doc_number")
    vcode = r.get("vendor_code")
    if not doc_no or doc_no == "—" or not vcode:
        continue
    
    key = (vcode, doc_no)
    if key not in invoices:
        invoices[key] = []
    invoices[key].append(r)

print("Total Unique MSME Invoices:", len(invoices))

# Calculate breaches
breaches_count = 0
for key, doc_rows in invoices.items():
    # Sort doc_rows by posting_date/document_date to find latest state
    doc_date = None
    for r in doc_rows:
        d_str = r.get("document_date") or r.get("posting_date")
        dt = fast_parse_date(d_str)
        if dt:
            if doc_date is None or dt < doc_date:
                doc_date = dt
                
    if not doc_date:
        continue
    
    # Check if there is any payment
    pay_date = None
    for r in doc_rows:
        p_str = r.get("payment_date")
        dt = fast_parse_date(p_str)
        if dt:
            if pay_date is None or dt > pay_date:
                pay_date = dt
                    
    latest_row = doc_rows[-1]
    status = latest_row.get("status")
    outstanding = abs(float(latest_row.get("outstanding") or 0.0))
    
    is_paid = status == 'Fully paid' or (pay_date is not None and outstanding <= 1.0)
    
    if is_paid:
        if pay_date:
            diff_days = (pay_date - doc_date).days
            if diff_days > 45:
                breaches_count += 1
    else:
        diff_days = (max_date - doc_date).days
        if diff_days > 45:
            breaches_count += 1

print("MSME breaches with fast invoice grouping:", breaches_count)
