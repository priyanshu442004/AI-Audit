import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis import po_status, gate_entry

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
FILE_MAPPING = {
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

def check_row_counts():
    dfs = {}
    for role, filename in FILE_MAPPING.items():
        filepath = os.path.join(EXCEL_DIR, filename)
        if os.path.exists(filepath):
            dfs[role] = pd.read_csv(filepath, low_memory=False)
            print(f"Loaded {role}: {len(dfs[role])} rows")
        else:
            print(f"Error: {filepath} not found.")
            return

    # Check PO Status Row Counts
    po_df = dfs["purchase_order"]
    # Check number of valid PO Numbers in original file
    col_po_no = po_status.find_col(po_df, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
    valid_po_count = 0
    if col_po_no:
        valid_po_count = sum(1 for x in po_df[col_po_no].dropna() if po_status.normalize_id(x).lower() not in ("", "nan", "none", "null"))
    
    print("\n--- Running PO Status Module ---")
    po_result = po_status.run(dfs)
    po_table_rows = po_result["tables"][3]["rows"] if "tables" in po_result and len(po_result["tables"]) > 3 else []
    print(f"Original PO File Rows: {len(po_df)}")
    print(f"Valid PO Numbers in File: {valid_po_count}")
    print(f"PO Status Output Table Rows: {len(po_table_rows)}")
    
    # Check Gate Entry Row Counts
    ge_df = dfs["gate_entry"]
    # Check number of valid Gate Entry Numbers in original file
    col_ge_no = gate_entry.find_col(ge_df, ["gate entry no", "gate entry no.", "ge no", "ge no.", "gate entry number", "security entry no", "security entry number"])
    valid_ge_count = 0
    if col_ge_no:
        valid_ge_count = sum(1 for x in ge_df[col_ge_no].dropna() if gate_entry.normalize_id(x).lower() not in ("", "nan", "none", "null"))
        
    print("\n--- Running Gate Entry Module ---")
    ge_result = gate_entry.run(dfs)
    ge_table_rows = ge_result["tables"][1]["rows"] if "tables" in ge_result and len(ge_result["tables"]) > 1 else []
    print(f"Original Gate Entry File Rows: {len(ge_df)}")
    print(f"Valid Gate Entry Numbers in File: {valid_ge_count}")
    print(f"Gate Entry Output Table Rows: {len(ge_table_rows)}")

if __name__ == "__main__":
    check_row_counts()
