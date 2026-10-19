import sys
import os
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import load_combined_dfs
from app.analysis.po_status import clean_num, safe_parse_date, find_col

dfs = load_combined_dfs(entity="ITL", process="P2P")
grpo_df = dfs.get("grpo")

grpo = grpo_df.copy()

TARGET_COLS = [
    'Gate Entry No', 'PO Number', 'GRPO No', 'Series Name', 'Posting Date',
    'Delivery Date', 'Document Date', 'Vendor Ref No', 'Branch', 'Document Status',
    'Canceled Status', 'Group Name', 'Vendor Code', 'Vendor Name', 'Item Group',
    'Item Code', 'Item Description', 'UOM', 'GRPO Qty', 'GRPO Price',
    'Document Currency', 'Document Rate', 'Line Total', 'Document Total',
    'Warehouse Code', 'Account Code'
]

# Ensure exact 26 target columns exist in exact order
for col in TARGET_COLS:
    if col not in grpo.columns:
        found = find_col(grpo, [col])
        if found:
            grpo[col] = grpo[found]
        else:
            grpo[col] = ""

grpo_26 = grpo[TARGET_COLS].copy()

grpo_26['GRPO_Qty_Num'] = clean_num(grpo_26['GRPO Qty']).fillna(0.0)
grpo_26['Line_Total_Num'] = clean_num(grpo_26['Line Total']).fillna(0.0)

po_str = grpo_26['PO Number'].astype(str).str.strip()
is_po_missing = grpo_26['PO Number'].isna() | po_str.isin(['', '0', '0.0', 'nan', 'None', '—', '-'])

missing_df = grpo_26[is_po_missing].copy()

def calc_kpis(subset_df: pd.DataFrame, label: str):
    total_count = len(subset_df)
    unique_grpo = int(subset_df['GRPO No'].nunique()) if not subset_df.empty else 0
    sum_qty = float(subset_df['GRPO_Qty_Num'].sum()) if not subset_df.empty else 0.0
    sum_val = float(subset_df['Line_Total_Num'].sum()) if not subset_df.empty else 0.0

    print(f"\n================ {label} ================")
    print(f"1. Total Count       : {total_count:,}")
    print(f"2. Unique GRPO       : {unique_grpo:,}")
    print(f"3. Sum of GRPO QTY   : {sum_qty:,.2f}")
    if sum_val >= 1e7:
        val_fmt = f"₹{(sum_val/1e7):.2f} Cr"
    elif sum_val >= 1e5:
        val_fmt = f"₹{(sum_val/1e5):.2f} Lakh"
    else:
        val_fmt = f"₹{sum_val:,.2f}"
    print(f"4. Sum of GRPO Value : {val_fmt}")

foc_mask = missing_df['Series Name'].astype(str).str.strip().str.upper().str.startswith('FOC')
foc_df = missing_df[foc_mask]
calc_kpis(foc_df, "FOC ITEMS SHEET")

jw_mask = missing_df['Group Name'].astype(str).str.strip().str.upper() == 'JOB WORK VENDOR'
jw_df = missing_df[jw_mask]
calc_kpis(jw_df, "JOB WORK ITEMS SHEET")

rep_mask = missing_df['Item Group'].astype(str).str.strip() == 'Rep & Maint Mach'
rep_df = missing_df[rep_mask]
calc_kpis(rep_df, "REPAIR & MAINTENANCE ITEMS SHEET")
