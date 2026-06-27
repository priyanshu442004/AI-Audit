import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import FILE_ROLES
from app.analysis.gate_entry import normalize_id

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
files = os.listdir(EXCEL_DIR)
dfs = {}

for role, match_str in FILE_ROLES.items():
    for f in files:
        if match_str.lower() in f.lower() and f.endswith(".csv"):
            dfs[role] = pd.read_csv(os.path.join(EXCEL_DIR, f), dtype=str)
            break

df_po = dfs.get("purchase_order")
df_ge = dfs.get("gate_entry")

po_no_col_po = "PO No"
po_no_col_ge = "Purchase Order Number"

po_set_po = {normalize_id(x) for x in df_po[po_no_col_po].dropna()}
print(f"Total unique PO numbers in PO sheet: {len(po_set_po)}")
print("Sample POs in PO sheet:", list(po_set_po)[:10])

ge_pos_raw = df_ge[po_no_col_ge].dropna().unique()
print(f"Total unique PO numbers in GE sheet: {len(ge_pos_raw)}")
print("Sample POs in GE sheet (raw):", list(ge_pos_raw)[:10])

matched = 0
unmatched_samples = []

for ge_po in ge_pos_raw:
    parts = [normalize_id(p) for p in str(ge_po).split(",") if normalize_id(p)]
    for p in parts:
        if p in po_set_po:
            matched += 1
            break
    else:
        unmatched_samples.append(ge_po)

print(f"Unique GE rows with at least one matching PO in PO sheet: {matched}")
print(f"Unmatched GE PO number samples: {unmatched_samples[:15]}")
