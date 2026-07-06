import pandas as pd
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.three_way_matching import run_three_way_matching

folder = r"C:\Users\hp\Desktop\excel files"

# Load files
print("Loading files...")
dfs = {
    "ap_invoice_report": pd.read_csv(os.path.join(folder, "AP Invoice Report ITL.csv")),
    "grpo": pd.read_csv(os.path.join(folder, "GRPO Report ITL.csv")),
    "purchase_order": pd.read_csv(os.path.join(folder, "Purchase Order Report-ITL.csv")),
    "gate_entry": pd.read_csv(os.path.join(folder, "Gate Entry Report-ITL.csv")),
    "ap_credit_note": pd.read_csv(os.path.join(folder, "AP Credit Note-ITL.csv")),
}

print("Running three way matching...")
res = run_three_way_matching(dfs)
print("KPIs calculated:")
print(res["kpis"])
print(f"Total rows in output: {len(res['rows'])}")
if len(res['rows']) > 0:
    print("First row sample:")
    print(res['rows'][0])
