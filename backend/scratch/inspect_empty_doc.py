import pandas as pd
from app.analysis.payment_aging_domestic import run_payment_aging_domestic

gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
bp_path = r"C:\Users\hp\Desktop\excel files\BP Master-ITL.csv"
po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"

df_gl = pd.read_csv(gl_path)
df_po = pd.read_csv(po_path)
df_bp = pd.read_csv(bp_path)

dfs = {
    "general_ledger": df_gl,
    "purchase_order": df_po,
    "vendor_master": df_bp
}

result = run_payment_aging_domestic(dfs)
rows = result["rows"]

empty_doc_rows = [r for r in rows if r["invoice_doc_number"].strip() == ""]
print(f"Number of rows with empty invoice_doc_number: {len(empty_doc_rows)}")
for i, r in enumerate(empty_doc_rows[:5]):
    print(f"Row {i+1}:")
    print(f"  vendor_code: {r['vendor_code']}")
    print(f"  vendor_name: {r['vendor_name']}")
    print(f"  document_date: {r['document_date']}")
    print(f"  posting_date: {r['posting_date']}")
    print(f"  outstanding: {r['outstanding']}")
