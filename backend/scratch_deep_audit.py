import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from app.loaders import load_file
from app.cleaning import detect_columns, rename_canonical
from app.config import COLUMN_ALIASES

folder = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"
files_in_folder = {
    "BP MASTER-S.xls": "vendor_master",
    "Item Master ISPL.xls": "item_master",
    "Purchase Order Report.xls": "purchase_order",
    "Gate Entry Report.xls": "gate_entry",
    "GRPO Report Item Wise.xls": "grpo",
    "Purchase Register Item Wise ISPL-C.xls": "purchase_register",
    "General Ledger.xls": "general_ledger",
    "AP Credit Note-C.xls": "ap_credit_note",
}

EXPECTED_CANONICALS = {
    "vendor_master": ["vendor_code", "vendor_name", "msme_category", "gstin", "pan", "state"],
    "item_master": ["item_code", "item_description"],
    "purchase_order": ["po_no", "po_date", "vendor_code", "vendor_name", "item_code", "item_description", "po_qty", "unit_price", "line_total", "po_status"],
    "gate_entry": ["ge_no", "ge_date", "vendor_code", "vendor_name", "vendor_bill_no", "vendor_bill_date"],
    "grpo": ["grpo_no", "grpo_date", "vendor_code", "vendor_name", "item_code", "item_description", "grpo_qty", "grpo_rate", "grpo_amount", "ge_no"],
    "purchase_register": ["invoice_no", "invoice_date", "vendor_code", "vendor_name", "item_code", "po_qty", "grpo_rate", "ge_grpo_no"],
    "general_ledger": ["gl_date", "vendor_code", "debit", "credit", "gl_ref", "trans_type"],
    "ap_credit_note": ["invoice_no", "invoice_date", "vendor_code", "vendor_name", "line_total"]
}

print("="*100)
print("DEEP AUDIT REPORT FOR ALL 8 INPUT FILES (ISPL P2P)")
print("="*100 + "\n")

results = {}

for filename, role in files_in_folder.items():
    filepath = os.path.join(folder, filename)
    print(f"\n" + "#"*80)
    print(f"FILE: {filename}  | ROLE: {role}")
    print("#"*80)
    
    try:
        df = load_file(filepath, filename)
        col_map = detect_columns(df)
        
        detected_canonicals = list(col_map.keys())
        expected = EXPECTED_CANONICALS.get(role, [])
        missing = [c for c in expected if c not in detected_canonicals]
        
        print(f"Total Rows: {len(df):,}")
        print(f"Total Columns: {len(df.columns)}")
        print(f"\n-> Detected Canonical Mappings:")
        for canon, orig in col_map.items():
            print(f"   * {canon:20s} <-- Header: '{orig}'")
            
        print(f"\n-> Missing Key Canonicals for {role}:")
        if missing:
            for m in missing:
                print(f"   WARNING: Missing '{m}'")
        else:
            print("   None! All expected canonical columns detected.")
            
        print(f"\n-> Unmapped Headers ({len(df.columns) - len(col_map)}):")
        mapped_origs = set(col_map.values())
        unmapped = [c for c in df.columns if c not in mapped_origs]
        print(f"   {unmapped[:10]}")
        if len(unmapped) > 10:
            print(f"   ... and {len(unmapped)-10} more unmapped headers")
            
        # Data Quality check on detected canonical columns
        print(f"\n-> Data Quality Details on Key Columns:")
        for canon, orig in col_map.items():
            series = df[orig]
            total = len(series)
            null_mask = series.isna() | (series.astype(str).str.strip() == '') | (series.astype(str).str.lower().isin(['nan', 'none', 'null']))
            null_count = null_mask.sum()
            null_pct = (null_count / total) * 100 if total > 0 else 0
            
            # Check unique counts and sample values
            non_null_vals = series[~null_mask].astype(str).str.strip()
            unique_cnt = non_null_vals.nunique()
            samples = non_null_vals.head(3).tolist()
            
            print(f"   * Column '{orig}' (Canonical: {canon})")
            print(f"     Nulls: {null_count:,} / {total:,} ({null_pct:.2f}%) | Unique: {unique_cnt:,} | Samples: {samples}")
            
        results[role] = {
            "filename": filename,
            "df": df,
            "col_map": col_map,
            "missing": missing
        }
            
    except Exception as e:
        print(f"ERROR reading {filename}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*100)
print("CROSS-FILE MASTER DATA & TRANSACTION LINKAGE DISCREPANCIES")
print("="*100)

# 1. Vendor Master Coverage
if "vendor_master" in results:
    vm_df = results["vendor_master"]["df"]
    vm_map = results["vendor_master"]["col_map"]
    vm_codes = set()
    if "vendor_code" in vm_map:
        vm_codes = set(vm_df[vm_map["vendor_code"]].dropna().astype(str).str.strip())
        print(f"\n1. VENDOR MASTER TOTAL CODES: {len(vm_codes):,}")
    
    for r in ["purchase_order", "grpo", "purchase_register", "general_ledger", "gate_entry"]:
        if r in results and "vendor_code" in results[r]["col_map"]:
            r_df = results[r]["df"]
            r_col = results[r]["col_map"]["vendor_code"]
            r_codes = set(r_df[r_col].dropna().astype(str).str.strip()) - {'', 'nan', 'None'}
            missing_vm = r_codes - vm_codes
            print(f"   - {r} ('{results[r]['filename']}'): {len(r_codes):,} unique vendors, {len(missing_vm):,} missing from BP Master")
            if missing_vm:
                print(f"     Missing samples: {list(missing_vm)[:5]}")

# 2. Item Master Coverage
if "item_master" in results:
    im_df = results["item_master"]["df"]
    im_map = results["item_master"]["col_map"]
    im_codes = set()
    if "item_code" in im_map:
        im_codes = set(im_df[im_map["item_code"]].dropna().astype(str).str.strip())
        print(f"\n2. ITEM MASTER TOTAL CODES: {len(im_codes):,}")
        
    for r in ["purchase_order", "grpo", "purchase_register"]:
        if r in results and "item_code" in results[r]["col_map"]:
            r_df = results[r]["df"]
            r_col = results[r]["col_map"]["item_code"]
            r_codes = set(r_df[r_col].dropna().astype(str).str.strip()) - {'', 'nan', 'None'}
            missing_im = r_codes - im_codes
            print(f"   - {r} ('{results[r]['filename']}'): {len(r_codes):,} unique items, {len(missing_im):,} missing from Item Master")
            if missing_im:
                print(f"     Missing samples: {list(missing_im)[:5]}")

# 3. PO Linkage across files
if "purchase_order" in results:
    po_df = results["purchase_order"]["df"]
    po_map = results["purchase_order"]["col_map"]
    po_numbers = set()
    if "po_no" in po_map:
        po_numbers = set(po_df[po_map["po_no"]].dropna().astype(str).str.strip()) - {'', 'nan', 'None'}
        print(f"\n3. PO REPORT TOTAL PO NUMBERS: {len(po_numbers):,}")
        
    for r in ["grpo", "purchase_register", "gate_entry"]:
        if r in results:
            r_df = results[r]["df"]
            r_map = results[r]["col_map"]
            # Look for po_no or base_po canonical
            po_col = r_map.get("po_no") or r_map.get("pr_po_no") or r_map.get("grpo_base_po")
            if po_col:
                r_pos = set(r_df[po_col].dropna().astype(str).str.strip()) - {'', 'nan', 'None'}
                missing_po = r_pos - po_numbers
                print(f"   - {r} ('{results[r]['filename']}'): {len(r_pos):,} unique PO refs, {len(missing_po):,} missing from PO Report")
                if missing_po:
                    print(f"     Missing samples: {list(missing_po)[:5]}")
