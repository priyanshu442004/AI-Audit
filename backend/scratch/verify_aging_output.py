import pandas as pd
import numpy as np
from app.analysis.payment_aging_domestic import run_payment_aging_domestic

gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
bp_path = r"C:\Users\hp\Desktop\excel files\BP Master-ITL.csv"
po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"

print("Loading real CSV files...")
df_gl = pd.read_csv(gl_path)
df_po = pd.read_csv(po_path)
df_bp = pd.read_csv(bp_path)

dfs = {
    "general_ledger": df_gl,
    "purchase_order": df_po,
    "vendor_master": df_bp
}

print("Computing payment aging analysis...")
result = run_payment_aging_domestic(dfs)
rows = result["rows"]
print(f"Total rows generated: {len(rows)}")

if len(rows) == 0:
    print("WARNING: No rows generated!")
    exit(1)

# Check for empty columns
columns = [
    "vendor_code", "vendor_name", "vendor_country", "vendor_group", "vendor_address",
    "payment_terms", "payment_term_type", "term_days", "invoice_doc_number", "document_date",
    "posting_date", "due_date_doc_term", "payment_date", "days_late", "actual_paid",
    "outstanding", "status", "aging_category"
]

null_counts = {col: 0 for col in columns}
empty_string_counts = {col: 0 for col in columns}
placeholder_counts = {col: 0 for col in columns}

for idx, r in enumerate(rows):
    for col in columns:
        val = r.get(col)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            null_counts[col] += 1
        elif str(val).strip() == "":
            empty_string_counts[col] += 1
        elif str(val).strip() == "—" or str(val).strip() == "nan" or str(val).strip() == "None":
            placeholder_counts[col] += 1

print("\n--- Column Incomplete/Null Check ---")
for col in columns:
    nulls = null_counts[col]
    empties = empty_string_counts[col]
    placeholders = placeholder_counts[col]
    print(f"Column '{col}': Nulls={nulls}, Empty Strings={empties}, Placeholders/Dash={placeholders}")

print("\nValidation complete. Let's inspect the first 5 rows:")
for i in range(min(5, len(rows))):
    print(f"\nRow {i+1}:")
    for col in columns:
        print(f"  {col}: {rows[i][col]}")
