import os
import sys
import pandas as pd
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.analysis.gate_entry import run as run_gate_entry
from app.analysis.po_status import run as run_po_status
from app.config import FILE_ROLES

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"

# Map files to roles
files = os.listdir(EXCEL_DIR)
dfs = {}

for role, match_str in FILE_ROLES.items():
    # Find file
    matched_file = None
    for f in files:
        if match_str.lower() in f.lower() and f.endswith(".csv"):
            matched_file = f
            break
    if matched_file:
        path = os.path.join(EXCEL_DIR, matched_file)
        print(f"Loading {matched_file} as role {role}...")
        dfs[role] = pd.read_csv(path, dtype=str)
    else:
        print(f"WARNING: No file found for role {role}")

print("\n--- RUNNING GATE ENTRY ANALYSIS ---")
try:
    res_ge = run_gate_entry(dfs)
    ge_table = next(t for t in res_ge["tables"] if "Full Transaction" in t["title"])
    ge_rows = ge_table["rows"]
    print(f"Gate Entry total rows: {len(ge_rows)}")
    
    # Print first 5 rows' details
    print("Sample rows:")
    cols_to_print = ["Gate Entry number", "PO Number", "GRN Number", "AP Invoice Number", "Item Code", "Item Description", "Quantity", "Rate(INR)", "Value(INR)", "GRPO Date"]
    for i, row in enumerate(ge_rows[:5]):
        print(f"\nRow {i+1}:")
        for col in cols_to_print:
            print(f"  {col}: {row.get(col, 'MISSING')}")
            
    # Count how many rows have non-empty PO Number, GRN Number, AP Invoice Number, Item Code
    non_empty_po = sum(1 for r in ge_rows if r.get("PO Number") not in ("—", "", None))
    non_empty_grn = sum(1 for r in ge_rows if r.get("GRN Number") not in ("—", "", None))
    non_empty_ap = sum(1 for r in ge_rows if r.get("AP Invoice Number") not in ("—", "", None))
    non_empty_item = sum(1 for r in ge_rows if r.get("Item Code") not in ("—", "", None))
    print(f"\nSummary of filled columns:")
    print(f"  PO Number populated: {non_empty_po} / {len(ge_rows)}")
    print(f"  GRN Number populated: {non_empty_grn} / {len(ge_rows)}")
    print(f"  AP Invoice Number populated: {non_empty_ap} / {len(ge_rows)}")
    print(f"  Item Code populated: {non_empty_item} / {len(ge_rows)}")

except Exception as e:
    print("ERROR RUNNING GATE ENTRY:")
    traceback.print_exc()

print("\n--- RUNNING PO STATUS ANALYSIS ---")
try:
    res_po = run_po_status(dfs)
    po_table = next(t for t in res_po["tables"] if "Purchase Order Line Status" in t["title"])
    po_rows = po_table["rows"]
    print(f"PO Status total rows: {len(po_rows)}")
    
    # Print first 10 rows' AP details
    print("\nSample PO lines with AP/CN:")
    printed = 0
    for r in po_rows:
        ap = r.get("AP Invoice No.")
        cn = r.get("AP Credit Note")
        if ap and ap != "—":
            print(f"  PO Number: {r.get('PO Number')}, Item: {r.get('Item code')}, AP: {ap}, CN: {cn}")
            printed += 1
            if printed >= 10:
                break
                
    non_empty_ap_po = sum(1 for r in po_rows if r.get("AP Invoice No.") not in ("—", "", None))
    non_empty_cn_po = sum(1 for r in po_rows if r.get("AP Credit Note") not in ("—", "", None))
    non_empty_grn_po = sum(1 for r in po_rows if r.get("GRN No.") not in ("—", "", None))
    print(f"\nSummary of PO Status filled columns:")
    print(f"  GRN No populated: {non_empty_grn_po} / {len(po_rows)}")
    print(f"  AP Invoice No populated: {non_empty_ap_po} / {len(po_rows)}")
    print(f"  AP Credit Note No populated: {non_empty_cn_po} / {len(po_rows)}")
    
except Exception as e:
    print("ERROR RUNNING PO STATUS:")
    traceback.print_exc()
