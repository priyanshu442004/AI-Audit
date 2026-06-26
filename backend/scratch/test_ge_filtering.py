import os
import sys
import pandas as pd

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.gate_entry import run as run_gate_entry

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

res = run_gate_entry(dfs)
rows = res["tables"][1]["rows"]

print(f"Total rows in analysis: {len(rows)}")

# Check if there are empty or nan Gate Entry numbers in the result
nan_ge_count = 0
empty_ge_count = 0
for idx, r in enumerate(rows):
    ge_num = r.get("Gate Entry number")
    if pd.isna(ge_num) or str(ge_num).lower() in ("nan", "none", "null"):
        nan_ge_count += 1
    elif str(ge_num).strip() == "":
        empty_ge_count += 1

print(f"NaN Gate Entry Numbers: {nan_ge_count}")
print(f"Empty Gate Entry Numbers: {empty_ge_count}")

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
