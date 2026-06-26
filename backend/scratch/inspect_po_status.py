import os
import sys
import pandas as pd

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.loaders import load_file
from app.analysis.po_status import run as run_po_status

excel_dir = r"C:\Users\hp\Desktop\excel files"
file_mapping = {
    'ap_credit_note': 'AP Credit Note-ITL.csv',
    'ap_invoice_report': 'AP Invoice Report ITL.csv',
    'vendor_master': 'BP Master-ITL.csv',
    'gate_entry': 'Gate Entry Report-ITL.csv',
    'general_ledger': 'General Ledger ITL.csv',
    'grpo': 'GRPO Report ITL.csv',
    'item_master': 'Item Master-ITL.csv',
    'purchase_order': 'Purchase Order Report-ITL.csv',
    'purchase_register': 'Purchase Register -ITL.csv'
}

print("Loading files...")
dfs = {}
for role, filename in file_mapping.items():
    filepath = os.path.join(excel_dir, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath, low_memory=False)
        dfs[role] = df
        print(f"  {role}: {df.shape[0]} rows")
    else:
        print(f"  Missing: {filename}")

if 'purchase_order' in dfs:
    po_df = dfs['purchase_order']
    print("\nPurchase Order columns:", list(po_df.columns))
    
    # Run PO status analysis
    result = run_po_status(dfs)
    print("\nPO Status KPIs:")
    for k, v in result['kpis'].items():
        print(f"  {k}: {v}")
        
    tables = result['tables']
    print("\nTables:")
    for t in tables:
        rows = t['rows']
        print(f"  Table '{t['title']}': {len(rows)} rows")
        if rows:
            print(f"    Sample columns: {list(rows[0].keys())}")
            # Check for NaN / blanks in first few rows
            for i, r in enumerate(rows[:5]):
                print(f"    Row {i}: PO Number={r.get('PO Number') or r.get('PO No')}, Vendor={r.get('Vendor Code') or r.get('Vendor_Code')}, Date={r.get('Document Date') or r.get('PO Date')}")
