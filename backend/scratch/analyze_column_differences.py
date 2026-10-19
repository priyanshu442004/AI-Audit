import os
import sys
import glob
import pandas as pd
import json

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.loaders import load_file

ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\p2p newww data\P2P - ISPL & Consumption ITL\P2P - ISPL ( CSV )"
itl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P New Q2 Data"

ispl_files = {
    "ap_credit_note": "AP Credit Note-C.csv",
    "ap_invoice_report": "AP Invoice Report-C.csv",
    "vendor_master": "BP MASTER-S.csv",
    "gate_entry": "Gate Entry Report.csv",
    "general_ledger": "General Ledger.csv",
    "grpo": "GRPO Report Item Wise.csv",
    "item_master": "Item Master ISPL.csv",
    "purchase_order": "Purchase Order Report.csv",
    "purchase_register": "Purchase Register Item Wise ISPL-C.csv",
}

itl_files = {
    "ap_credit_note": "AP Credit Note-ITL1.xls",
    "ap_invoice_report": "AP Invoice Report ITL1.xls",
    "vendor_master": "BP Master-ITL1.xls",
    "gate_entry": "Gate Entry Report ITL.xls",
    "general_ledger": "General Ledger Report ITL1.xls",
    "grpo": "new GRPO Report-ITL1.xls",
    "item_master": "Item Master-ITL.xls",
    "purchase_order": "Purchase Order Report ITL.xls",
    "purchase_register": "Purchase Register Item Wise - ITL.xls",
}

print("=========================================================================")
print("COMPARISON: ISPL CSV COLUMNS vs ITL XLS COLUMNS ACROSS ALL 9 FILE ROLES")
print("=========================================================================\n")

for role in ispl_files.keys():
    ispl_fname = ispl_files[role]
    ispl_path = os.path.join(ispl_dir, ispl_fname)
    ispl_cols = []
    if os.path.exists(ispl_path):
        with open(ispl_path, 'rb') as f:
            df = load_file(f, ispl_fname)
            ispl_cols = list(df.columns)
            
    itl_fname = itl_files[role]
    itl_path = os.path.join(itl_dir, itl_fname)
    itl_cols = []
    if os.path.exists(itl_path):
        with open(itl_path, 'rb') as f:
            df_itl = load_file(f, itl_fname)
            itl_cols = list(df_itl.columns)

    print(f"### ROLE: {role.upper()}")
    print(f"ISPL File: {ispl_fname} ({len(ispl_cols)} cols)")
    print(f"ITL  File: {itl_fname} ({len(itl_cols)} cols)")
    
    in_ispl_not_itl = [c for c in ispl_cols if c not in itl_cols]
    in_itl_not_ispl = [c for c in itl_cols if c not in ispl_cols]
    common = [c for c in ispl_cols if c in itl_cols]
    
    print(f"  - Common Columns ({len(common)}): {common}")
    if in_itl_not_ispl:
        print(f"  [!] In ITL but DIFFERENT/MISSING in ISPL ({len(in_itl_not_ispl)}): {in_itl_not_ispl}")
    if in_ispl_not_itl:
        print(f"  [+] In ISPL but DIFFERENT/MISSING in ITL ({len(in_ispl_not_itl)}): {in_ispl_not_itl}")
    print("-" * 75)
