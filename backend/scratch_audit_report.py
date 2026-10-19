import os
import sys
import pandas as pd
import numpy as np

# Ensure app package can be imported
sys.path.insert(0, os.path.dirname(__file__))

from app.loaders import load_file
from app.cleaning import detect_columns, rename_canonical, parse_numeric, parse_dates
from app.config import COLUMN_ALIASES

folder = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"
files_in_folder = {
    "AP Credit Note-C.xls": "ap_credit_note",
    "BP MASTER-S.xls": "vendor_master",
    "Gate Entry Report.xls": "gate_entry",
    "General Ledger.xls": "general_ledger",
    "GRPO Report Item Wise.xls": "grpo",
    "Item Master ISPL.xls": "item_master",
    "Purchase Order Report.xls": "purchase_order",
    "Purchase Register Item Wise ISPL-C.xls": "purchase_register",
}

print("================================================================================")
print("COMPREHENSIVE AUDIT ANALYSIS FOR ISPL P2P FILES IN SQL SERVER DIRECTORY")
print("================================================================ algorithm\n")

loaded_dfs = {}

for filename, role in files_in_folder.items():
    filepath = os.path.join(folder, filename)
    print(f"\n" + "="*80)
    print(f"FILE: {filename}")
    print(f"ROLE: {role}")
    print("="*80)

    if not os.path.exists(filepath):
        print(f"ERROR: File not found at {filepath}")
        continue

    try:
        df_raw = load_file(filepath, filename)
        print(f"Raw Loaded Shape: {df_raw.shape[0]} rows, {df_raw.shape[1]} columns")
        print(f"Raw Column Names: {list(df_raw.columns)}")
        
        # Column mapping detection
        col_map = detect_columns(df_raw)
        print(f"\nDetected Canonical Mappings ({len(col_map)}):")
        for canon, orig in col_map.items():
            print(f"  - '{orig}'  -->  canonical: '{canon}'")
        
        # Cleaned/Renamed dataframe
        df_clean = rename_canonical(df_raw, col_map)
        print(f"\nRenamed Shape: {df_clean.shape[0]} rows, {df_clean.shape[1]} columns")
        
        loaded_dfs[role] = {
            "filename": filename,
            "df_raw": df_raw,
            "df_clean": df_clean,
            "col_map": col_map
        }
        
        # Detailed Column Quality Check
        print("\n--- COLUMN LEVEL DATA QUALITY ANALYSIS ---")
        for col in df_raw.columns:
            series = df_raw[col]
            total = len(series)
            null_cnt = series.isna().sum() + (series.astype(str).str.strip() == '').sum() + (series.astype(str).str.lower().isin(['nan', 'none', 'null'])).sum()
            null_pct = (null_cnt / total) * 100 if total > 0 else 0
            
            non_null_samples = series.dropna().astype(str).str.strip()
            non_null_samples = non_null_samples[~non_null_samples.str.lower().isin(['', 'nan', 'none', 'null'])].head(3).tolist()
            
            canon_tag = [k for k, v in col_map.items() if v == col]
            tag_str = f" [CANONICAL: {canon_tag[0]}]" if canon_tag else " [UNMAPPED]"
            print(f" Raw Column: '{col}'{tag_str} | Nulls: {null_cnt}/{total} ({null_pct:.1f}%) | Samples: {non_null_samples}")

    except Exception as e:
        print(f"ERROR loading/parsing {filename}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("CROSS-FILE INTEGRITY AND RECONCILIATION AUDIT")
print("="*80)

# Check PO No overlap between PO Report, GRPO, Purchase Register, Gate Entry
po_nos = {}
for role in ["purchase_order", "grpo", "purchase_register", "gate_entry"]:
    if role in loaded_dfs and "po_no" in loaded_dfs[role]["df_clean"].columns:
        s = loaded_dfs[role]["df_clean"]["po_no"].dropna().astype(str).str.strip()
        s = set(s[s != ''])
        po_nos[role] = s
        print(f"Unique PO Nos in {role} ('{loaded_dfs[role]['filename']}'): {len(s)}")

if "purchase_order" in po_nos and "grpo" in po_nos:
    po_in_po = po_nos["purchase_order"]
    po_in_grpo = po_nos["grpo"]
    missing_in_po = po_in_grpo - po_in_po
    print(f"\nGRPO PO Nos not found in PO Report: {len(missing_in_po)} (Sample: {list(missing_in_po)[:5]})")

if "purchase_order" in po_nos and "purchase_register" in po_nos:
    po_in_po = po_nos["purchase_order"]
    po_in_pr = po_nos["purchase_register"]
    missing_in_po_pr = po_in_pr - po_in_po
    print(f"Purchase Register PO Nos not found in PO Report: {len(missing_in_po_pr)} (Sample: {list(missing_in_po_pr)[:5]})")

# Check Vendor Code overlap
vendor_codes = {}
for role in ["vendor_master", "purchase_order", "grpo", "purchase_register", "general_ledger"]:
    if role in loaded_dfs and "vendor_code" in loaded_dfs[role]["df_clean"].columns:
        s = loaded_dfs[role]["df_clean"]["vendor_code"].dropna().astype(str).str.strip()
        s = set(s[s != ''])
        vendor_codes[role] = s
        print(f"Unique Vendor Codes in {role} ('{loaded_dfs[role]['filename']}'): {len(s)}")

if "vendor_master" in vendor_codes:
    master_vendors = vendor_codes["vendor_master"]
    for role in ["purchase_order", "grpo", "purchase_register"]:
        if role in vendor_codes:
            unmatched = vendor_codes[role] - master_vendors
            print(f"Vendors in {role} not present in Vendor Master: {len(unmatched)} (Sample: {list(unmatched)[:5]})")

# Check Item Code overlap
item_codes = {}
for role in ["item_master", "purchase_order", "grpo", "purchase_register"]:
    if role in loaded_dfs and "item_code" in loaded_dfs[role]["df_clean"].columns:
        s = loaded_dfs[role]["df_clean"]["item_code"].dropna().astype(str).str.strip()
        s = set(s[s != ''])
        item_codes[role] = s
        print(f"Unique Item Codes in {role} ('{loaded_dfs[role]['filename']}'): {len(s)}")

if "item_master" in item_codes:
    master_items = item_codes["item_master"]
    for role in ["purchase_order", "grpo"]:
        if role in item_codes:
            unmatched = item_codes[role] - master_items
            print(f"Items in {role} not present in Item Master: {len(unmatched)} (Sample: {list(unmatched)[:5]})")
