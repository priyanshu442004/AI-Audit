import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

def parse_date(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", "", "—"):
        return None
    for fmt in ('%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
        try:
            return pd.to_datetime(val_str, format=fmt)
        except:
            continue
    try:
        return pd.to_datetime(val_str, errors='coerce')
    except:
        return None

def parse_numeric(val):
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).replace(",", "").strip()
    if val_str.lower() in ("nan", "none", "", "—"):
        return 0.0
    try:
        return float(val_str)
    except:
        return 0.0

# Paths
gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
bp_path = r"C:\Users\hp\Desktop\excel files\BP Master-ITL.csv"
po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"

# Load BP Master for payment terms
print("Loading BP Master...")
df_bp = pd.read_csv(bp_path)
bp_terms = {}
for _, row in df_bp.iterrows():
    code = str(row.get('BP Code', '')).strip()
    term = str(row.get('Payment Terms Code', '')).strip()
    if code:
        bp_terms[code] = term

# Load PO Report for country and group
print("Loading PO Report...")
df_po = pd.read_csv(po_path)
po_vendor_info = {}
for _, row in df_po.iterrows():
    vcode = str(row.get('Vendor Code', '')).strip()
    if not vcode:
        continue
    curr = str(row.get('Document Currency', '')).strip()
    group = str(row.get('Vendor Group', '')).strip()
    country = "India" if curr.upper() in ("INR", "") else "USA"
    if vcode not in po_vendor_info:
        po_vendor_info[vcode] = {'country': country, 'group': group}

# Parse General Ledger
print("Parsing General Ledger...")
rows = []
current_vendor_code = None
current_vendor_name = None

with open(gl_path, 'r', encoding='utf-8', errors='ignore') as f:
    import csv
    reader = csv.reader(f)
    header = next(reader)
    # Print header to be absolutely sure
    print("Header:", header)
    
    for row_idx, row in enumerate(reader):
        if not row:
            continue
        if len(row) < 2:
            continue
        
        # Check if it's a vendor header row
        if row[0] == 'Vendor':
            current_vendor_code = row[1].strip()
            current_vendor_name = row[9].strip() if len(row) > 9 else ""
            continue
        
        # If posting date is empty or invalid and we have no vendor, skip
        posting_date_str = row[0].strip()
        if not posting_date_str:
            continue
            
        if current_vendor_code is None:
            continue
            
        # Parse transaction details
        due_date_str = row[1].strip() if len(row) > 1 else ""
        doc_date_str = row[2].strip() if len(row) > 2 else ""
        doc_no = row[5].strip() if len(row) > 5 else ""
        debit_str = row[11].strip() if len(row) > 11 else ""
        credit_str = row[12].strip() if len(row) > 12 else ""
        cum_bal_str = row[13].strip() if len(row) > 13 else ""
        
        # 1. Vendor Country
        v_info = po_vendor_info.get(current_vendor_code, {})
        country = v_info.get('country', 'India')  # Default to India if not found
        
        # 2. Filter out non-Domestic (only keep India)
        if country != 'India':
            continue
            
        # 3. Vendor Group
        vendor_group = v_info.get('group', 'Domestic vendor')
        if not vendor_group or vendor_group == 'nan':
            vendor_group = 'Domestic vendor'
            
        # 4. Vendor Address (same as vendor name)
        vendor_address = current_vendor_name
        
        # 5. Payment Terms
        payment_terms = bp_terms.get(current_vendor_code, '—')
        
        # 6. Payment Term Type and Term Days
        term_type = "Advance"
        term_days = 0
        if pd.notna(payment_terms) and payment_terms != '—':
            term_clean = str(payment_terms).strip()
            # check for NET
            match = re.search(r'net[- ]?(\d+)', term_clean, re.IGNORECASE)
            if match:
                term_type = "Credit(Net)"
                term_days = int(match.group(1))
            elif "net" in term_clean.lower():
                term_type = "Credit(Net)"
                # try to extract any number
                num_match = re.search(r'\d+', term_clean)
                if num_match:
                    term_days = int(num_match.group(0))
        
        # 7. Dates
        doc_dt = parse_date(doc_date_str)
        post_dt = parse_date(posting_date_str)
        due_dt = parse_date(due_date_str)
        
        # 8. Due Date (Doc + Term)
        due_date_calc = None
        if doc_dt:
            due_date_calc = doc_dt + timedelta(days=term_days)
            
        # 9. Payment Date
        debit_val = parse_numeric(debit_str)
        credit_val = parse_numeric(credit_str)
        payment_date = "—"
        if debit_val > 0:
            payment_date = doc_date_str if doc_date_str else posting_date_str
            pay_dt = doc_dt if doc_dt else post_dt
        else:
            pay_dt = None
            
        # 10. Days Late
        days_late = 0
        if pay_dt and due_date_calc:
            diff = (pay_dt - due_date_calc).days
            days_late = max(0, diff)
            
        # 11. Actual Paid
        actual_paid = debit_val if debit_val > 0 else 0.0
        
        # 12. Outstanding
        outstanding = parse_numeric(cum_bal_str)
        
        # 13. Status
        if abs(outstanding) <= 0.01:
            status = "Fully paid"
        elif actual_paid == 0:
            status = "Open"
        else:
            status = "Partially paid"
            
        # 14. Aging Category
        if days_late <= 15:
            aging_cat = "Overdue 0-15"
        elif days_late <= 30:
            aging_cat = "Overdue 16-30"
        elif days_late <= 45:
            aging_cat = "Overdue 31-45"
        elif days_late <= 60:
            aging_cat = "Overdue 46-60"
        elif days_late <= 90:
            aging_cat = "Overdue 61-90"
        else:
            aging_cat = "Overdue >90"
            
        rows.append({
            "Vendor code": current_vendor_code,
            "Vendor Name": current_vendor_name,
            "Vendor Country": country,
            "Vendor Group": vendor_group,
            "Vendor Address": vendor_address,
            "Payment Terms": payment_terms,
            "Payment Term Type": term_type,
            "Term Days": term_days,
            "Invoice Doc Number": doc_no,
            "Document Date": doc_date_str if doc_date_str else "—",
            "Posting Date": posting_date_str if posting_date_str else "—",
            "Due Date(Doc+Term)": due_date_calc.strftime("%d/%m/%y") if due_date_calc else "—",
            "Payment Date": payment_date,
            "Days Late": days_late,
            "Actual Paid": actual_paid,
            "Outstanding": outstanding,
            "Status": status,
            "Aging Category": aging_cat
        })

print(f"Total processed rows: {len(rows)}")
df_res = pd.DataFrame(rows)
print("\nFirst 10 rows of result:")
print(df_res.head(10).to_string())

# Check for empty columns
print("\nChecking for missing/empty columns:")
print(df_res.isnull().sum())
print("Unique vendor codes:", len(df_res["Vendor code"].unique()))
print("Status counts:\n", df_res["Status"].value_counts())
