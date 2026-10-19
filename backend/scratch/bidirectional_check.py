import os
import glob
import csv
import pandas as pd

ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\p2p newww data\P2P - ISPL & Consumption ITL\P2P - ISPL ( CSV )"

# Read actual CSV file columns
actual_ispl_cols = {}
for filepath in glob.glob(os.path.join(ispl_dir, "*.csv")):
    fname = os.path.basename(filepath)
    df = pd.read_csv(filepath, nrows=1, encoding='utf-8-sig', low_memory=False)
    actual_ispl_cols[fname] = list(df.columns)

# Read Google Sheet rows for ISPL
with open('scratch/gsheet_raw.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    gsheet_rows = list(reader)

gsheet_ispl_cols = {}
for row in gsheet_rows:
    if not row or not row[1].strip():
        continue
    label = row[1].strip()
    cols = [c.strip() for c in row[2:] if c.strip()]
    gsheet_ispl_cols[label] = cols

mapping = [
    ("AP Credit Note-C.csv", "AP Credit Note-CISPL"),
    ("AP Invoice Report-C.csv", "AP Invoice Report-C ispl"),
    ("BP MASTER-S.csv", "ispl BP Master"),
    ("Gate Entry Report.csv", "Gate Entry Report ispl"),
    ("General Ledger.csv", "general ledger ispl"),
    ("GRPO Report Item Wise.csv", "GRPO Report Item Wise ispl"),
    ("Item Master ISPL.csv", "Item Master ISPL"),
    ("Purchase Order Report.csv", "Purchase Order Report -ISPL"),
    ("Purchase Register Item Wise ISPL-C.csv", "Purchase Register Item Wise ISP"),
]

print("=========================================================================")
print("BIDIRECTIONAL COLUMN AUDIT REPORT: GOOGLE SHEET vs ACTUAL ISPL CSV FILES")
print("=========================================================================\n")

anything_missing_in_files = False
anything_extra_in_files = False

for csv_name, gsheet_key in mapping:
    actual = actual_ispl_cols.get(csv_name, [])
    doc_cols = gsheet_ispl_cols.get(gsheet_key, [])
    
    actual_set = set(actual)
    doc_set = set(doc_cols)
    
    missing_in_files = [c for c in doc_cols if c not in actual_set]
    extra_in_files = [c for c in actual if c not in doc_set]
    
    print(f"--- File: {csv_name}  <-->  Document Label: [{gsheet_key}] ---")
    print(f"    Document defined columns count : {len(doc_cols)}")
    print(f"    Actual CSV file columns count  : {len(actual)}")
    
    if missing_in_files:
        anything_missing_in_files = True
        print(f"    [!] IN DOCUMENT BUT MISSING IN FILE ({len(missing_in_files)}): {missing_in_files}")
    else:
        print(f"    [OK] 0 columns in Document are missing in File.")
        
    if extra_in_files:
        anything_extra_in_files = True
        print(f"    [+] IN FILE BUT NOT IN DOCUMENT ({len(extra_in_files)}): {extra_in_files}")
    else:
        print(f"    [OK] 0 extra columns in File.")
    print("")

print("=========================================================================")
print(f"SUMMARY RESULT:")
print(f"  Any columns in Document missing in Files? -> {anything_missing_in_files}")
print(f"  Any columns in Files missing in Document? -> {anything_extra_in_files}")
print("=========================================================================")
