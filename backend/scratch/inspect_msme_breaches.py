import pickle
import os
import pandas as pd

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

with open(os.path.join(cache_dir, "aging_msme.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

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
max_date = max(dates) if dates else pd.to_datetime("2026-03-31")

print("Max Date:", max_date)

# Group rows by invoice_doc_number
invoices = {}
for r in rows:
    doc_no = r.get("invoice_doc_number")
    if not doc_no or doc_no == "—":
        continue
    
    # We want to collect all rows for this invoice to determine its doc_date, payment_date, outstanding and status
    if doc_no not in invoices:
        invoices[doc_no] = []
    invoices[doc_no].append(r)

print("Total Unique MSME Invoices:", len(invoices))

# Calculate breaches
breaches_count = 0
for doc_no, doc_rows in invoices.items():
    # Sort doc_rows by posting_date/document_date to find latest state
    # doc_date is from the earliest row or any row (usually same for all rows of same invoice)
    doc_dates = []
    for r in doc_rows:
        d_str = r.get("document_date") or r.get("posting_date")
        if d_str and d_str != '—':
            try:
                doc_dates.append(pd.to_datetime(d_str, format="%d/%m/%y"))
            except:
                try:
                    doc_dates.append(pd.to_datetime(d_str))
                except:
                    pass
    if not doc_dates:
        continue
    doc_date = min(doc_dates)
    
    # Check if there is any payment
    payment_dates = []
    for r in doc_rows:
        p_str = r.get("payment_date")
        if p_str and p_str != '—':
            try:
                payment_dates.append(pd.to_datetime(p_str, format="%d/%m/%y"))
            except:
                try:
                    payment_dates.append(pd.to_datetime(p_str))
                except:
                    pass
                    
    # Find latest status / outstanding
    # The last row in the list of transactions for this invoice
    # We can sort by posting_date
    latest_row = doc_rows[-1] # they are already sorted in the pkl
    status = latest_row.get("status")
    outstanding = abs(float(latest_row.get("outstanding") or 0.0))
    
    is_paid = status == 'Fully paid' or (len(payment_dates) > 0 and outstanding <= 1.0)
    
    if is_paid:
        if payment_dates:
            pay_date = max(payment_dates)
            diff_days = (pay_date - doc_date).days
            if diff_days > 45:
                breaches_count += 1
    else:
        diff_days = (max_date - doc_date).days
        if diff_days > 45:
            breaches_count += 1

print("MSME breaches with invoice grouping:", breaches_count)
