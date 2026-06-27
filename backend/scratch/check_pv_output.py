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

res = run_variance_analysis(dfs, "same")
rows = res.get("rows", [])
print(f"Total same-vendor rows: {len(rows)}")
if rows:
    print("Sample row:")
    for k, v in rows[0].items():
        print(f"  {k}: {repr(v)}")
    
    ge_date = rows[0].get("gate_entry_date")
    if ge_date:
        print(f"gate_entry_date ords: {[ord(c) for c in ge_date]}")
    
    # Check for empty/blank values
    empty_counts = {}
    for r in rows:
        for k, v in r.items():
            if v is None or str(v).strip() in ("", "nan", "None", "—"):
                empty_counts[k] = empty_counts.get(k, 0) + 1
    print("\nEmpty/Blank counts per column:")
    for k, v in empty_counts.items():
        print(f"  {k}: {v} / {len(rows)}")
