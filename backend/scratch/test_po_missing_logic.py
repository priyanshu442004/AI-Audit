import sys
import os
import pandas as pd

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import load_combined_dfs

dfs = load_combined_dfs(entity="ITL", process="P2P")
grpo_df = dfs.get("grpo")

if grpo_df is None:
    print("GRPO DF IS NONE")
    sys.exit(1)

# Clean PO Number
grpo_df['PO Number Str'] = grpo_df['PO Number'].astype(str).str.strip()
is_po_missing = (
    grpo_df['PO Number'].isna() | 
    grpo_df['PO Number Str'].isin(['', '0', '0.0', 'nan', 'None', '—', '-']) |
    (grpo_df['PO Number Str'] == '')
)

missing_df = grpo_df[is_po_missing].copy()
print(f"Total GRPO Rows: {len(grpo_df)}")
print(f"Total PO Missing GRPO Rows: {len(missing_df)}")

# Sheet 1: FOC Items (Series Name starts with FOC)
foc_mask = missing_df['Series Name'].astype(str).str.strip().str.upper().str.startswith('FOC')
foc_df = missing_df[foc_mask].copy()

# Sheet 2: Job Work Items (Group Name == 'JOB WORK VENDOR')
jw_mask = missing_df['Group Name'].astype(str).str.strip().str.upper() == 'JOB WORK VENDOR'
jw_df = missing_df[jw_mask].copy()

# Sheet 3: Repair & Maintenance Items (Item Group == 'Rep & Maint Mach')
rep_mask = missing_df['Item Group'].astype(str).str.strip() == 'Rep & Maint Mach'
rep_df = missing_df[rep_mask].copy()

print(f"\n--- 1. FOC ITEMS SHEET ---")
print(f"Rows: {len(foc_df)}")
print(f"Total Line Value: {foc_df['Line Total'].astype(str).str.replace(',', '').astype(float).sum():,.2f}")
print(f"Unique Vendors: {foc_df['Vendor Name'].nunique()}")

print(f"\n--- 2. JOB WORK ITEMS SHEET ---")
print(f"Rows: {len(jw_df)}")
print(f"Total Line Value: {jw_df['Line Total'].astype(str).str.replace(',', '').astype(float).sum():,.2f}")
print(f"Unique Vendors: {jw_df['Vendor Name'].nunique()}")

print(f"\n--- 3. REPAIR & MAINTENANCE ITEMS SHEET ---")
print(f"Rows: {len(rep_df)}")
print(f"Total Line Value: {rep_df['Line Total'].astype(str).str.replace(',', '').astype(float).sum():,.2f}")
print(f"Unique Vendors: {rep_df['Vendor Name'].nunique()}")
