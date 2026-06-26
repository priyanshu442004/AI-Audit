import os
import sys
import pandas as pd

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.po_status import run as run_po_status

excel_dir = r"C:\Users\hp\Desktop\excel files"
file_mapping = {
    'ap_credit_note': 'AP Credit Note-ITL.csv',
    'ap_invoice_report': 'AP Invoice Report ITL.csv',
    'vendor_master': 'BP Master-ITL.csv',
    'gate_entry': 'Gate Entry Report-ITL.csv',
    'grpo': 'GRPO Report ITL.csv',
    'purchase_order': 'Purchase Order Report-ITL.csv',
    'purchase_register': 'Purchase Register -ITL.csv'
}

dfs = {}
for role, filename in file_mapping.items():
    filepath = os.path.join(excel_dir, filename)
    if os.path.exists(filepath):
        dfs[role] = pd.read_csv(filepath, low_memory=False)

res = run_po_status(dfs)
rows = res["tables"][3]["rows"]

print(f"Total rows in analysis: {len(rows)}")

# Let's check if there are empty or nan PO numbers in the result
nan_po_count = 0
empty_po_count = 0
for idx, r in enumerate(rows):
    po_num = r.get("PO Number")
    if pd.isna(po_num) or str(po_num).lower() in ("nan", "none", "null"):
        nan_po_count += 1
    elif str(po_num).strip() == "":
        empty_po_count += 1

print(f"NaN PO Numbers: {nan_po_count}")
print(f"Empty PO Numbers: {empty_po_count}")

# Check columns for nan or blank values
cols_with_nans = {}
cols_with_blanks = {}
for r in rows:
    for col, val in r.items():
        if pd.isna(val) or str(val).lower() in ("nan", "none", "null"):
            cols_with_nans[col] = cols_with_nans.get(col, 0) + 1
        elif str(val).strip() == "":
            cols_with_blanks[col] = cols_with_blanks.get(col, 0) + 1

print("\nColumns with NaN/Null/None values:")
for col, cnt in cols_with_nans.items():
    print(f"  {col}: {cnt} rows")

print("\nColumns with blank values:")
for col, cnt in cols_with_blanks.items():
    print(f"  {col}: {cnt} rows")

# Let's inspect some of these rows to see what is happening
print("\nSample rows with NaN PO Numbers or Empty PO Numbers (first 5):")
count = 0
for idx, r in enumerate(rows):
    po_num = r.get("PO Number")
    if pd.isna(po_num) or str(po_num).lower() in ("nan", "none", "null", ""):
        print(f"  Row {idx}: {r}")
        count += 1
        if count >= 5:
            break
