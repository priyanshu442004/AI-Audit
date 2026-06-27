import os
import sys
import pandas as pd
import traceback
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.price_variance_new import run_variance_analysis
from app.config import FILE_ROLES

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"

# Map files to roles
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

print("Files loaded. Running price variance analysis (same vendor)...")
try:
    res = run_variance_analysis(dfs, "same")
    print("SUCCESS! Same-vendor analysis results:")
    print("Tables:", [t["title"] for t in res.get("tables", [])])
    if res.get("tables"):
        print("Rows count:", len(res["tables"][0]["rows"]))
except Exception as e:
    print("FAILED SAME VENDOR:")
    traceback.print_exc()

print("\nRunning price variance analysis (cross vendor)...")
try:
    res_cross = run_variance_analysis(dfs, "cross")
    print("SUCCESS! Cross-vendor analysis results:")
    print("Tables:", [t["title"] for t in res_cross.get("tables", [])])
    if res_cross.get("tables"):
        print("Rows count:", len(res_cross["tables"][0]["rows"]))
except Exception as e:
    print("FAILED CROSS VENDOR:")
    traceback.print_exc()
