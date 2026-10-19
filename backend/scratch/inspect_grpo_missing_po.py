import sys
import os
import pandas as pd

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import load_combined_dfs

dfs = load_combined_dfs(entity="ITL", process="P2P")
grpo_df = dfs.get("grpo")

print("ALL GRPO COLS:")
for col in grpo_df.columns:
    print(f"'{col}'")

# Look for PO Number / Base Ref / PO No in grpo_df
po_col = None
for col in grpo_df.columns:
    if 'po' in col.lower() or 'base' in col.lower() or 'order' in col.lower() or 'ref' in col.lower():
        print(f"Candidate PO col: '{col}' sample: {grpo_df[col].dropna().unique()[:5]}")
