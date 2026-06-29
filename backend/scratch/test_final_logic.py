import pandas as pd
import json
from app.analysis.payment_aging_domestic import run_payment_aging_domestic

print("Loading test CSVs...")
gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
bp_path = r"C:\Users\hp\Desktop\excel files\BP Master-ITL.csv"
po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"

# Load them as dataframes (which mimics backend)
df_gl = pd.read_csv(gl_path)
df_po = pd.read_csv(po_path)
df_bp = pd.read_csv(bp_path)

dfs = {
    "general_ledger": df_gl,
    "purchase_order": df_po,
    "vendor_master": df_bp
}

print("Running payment aging domestic analysis...")
result = run_payment_aging_domestic(dfs)
rows = result["rows"]
print(f"Success! Generated {len(rows)} rows.")
if rows:
    print("Sample row:", json.dumps(rows[0], indent=2))
