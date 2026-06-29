import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.price_variance_new import run_variance_analysis
from app.config import FILE_ROLES

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
files = os.listdir(EXCEL_DIR)
dfs = {}

for role, match_str in FILE_ROLES.items():
    matched_file = None
    for f in files:
        if match_str.lower() in f.lower() and f.endswith(".csv"):
            matched_file = f
            break
    if matched_file:
        path = os.path.join(EXCEL_DIR, matched_file)
        dfs[role] = pd.read_csv(path, dtype=str)
    else:
        dfs[role] = pd.DataFrame()

print("--- Same Vendor Analysis ---")
res_same = run_variance_analysis(dfs, "same")
rows_same = res_same.get("rows", [])
print(f"Total rows: {len(rows_same)}")
if rows_same:
    print("Sample row:")
    for k, v in rows_same[0].items():
        print(f"  {k}: {repr(v)}")

print("\n--- Cross Vendor Analysis ---")
res_cross = run_variance_analysis(dfs, "cross")
rows_cross = res_cross.get("rows", [])
print(f"Total rows: {len(rows_cross)}")
if rows_cross:
    print("Sample row:")
    for k, v in rows_cross[0].items():
        print(f"  {k}: {repr(v)}")

    # Check for empty/blank values in cross vendor rows
    empty_counts = {}
    for r in rows_cross:
        for k, v in r.items():
            if v is None or str(v).strip() in ("", "nan", "None"):
                # Note: vendor_position is allowed to be empty or "—" as per "others left blank"
                if k != "vendor_position":
                    empty_counts[k] = empty_counts.get(k, 0) + 1
    print("\nEmpty/Blank counts per column (excluding vendor_position):")
    for k, v in empty_counts.items():
        print(f"  {k}: {v} / {len(rows_cross)}")
