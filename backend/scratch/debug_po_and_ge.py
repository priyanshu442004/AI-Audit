import os
import sys
import pandas as pd
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.gate_entry import run as run_gate_entry
from app.analysis.po_status import run as run_po_status
from app.config import FILE_ROLES
from app.analysis.gate_entry import find_col

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

print("--- FILE COLUMNS ---")
for role, df in dfs.items():
    print(f"Role: {role}")
    print("  Columns:", list(df.columns[:15]))
    # check PO number column
    po_col = find_col(df, ["po no", "po no.", "po number", "purchase order no", "purchase order number", "docnum", "docentry", "order number", "doc no", "order no", "document no", "base ref"])
    print(f"  Detected PO Column: {po_col}")

print("\n--- RUNNING GATE ENTRY ---")
try:
    res_ge = run_gate_entry(dfs)
    print("Gate Entry tables returned:")
    for t in res_ge["tables"]:
        print(f"  Title: {t['title']}, Row count: {len(t['rows'])}")
except Exception:
    traceback.print_exc()

print("\n--- RUNNING PO STATUS ---")
try:
    res_po = run_po_status(dfs)
    print("PO Status tables returned:")
    for t in res_po["tables"]:
        print(f"  Title: {t['title']}, Row count: {len(t['rows'])}")
except Exception:
    traceback.print_exc()
