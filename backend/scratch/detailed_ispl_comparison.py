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

print("=== GOOGLE SHEET ISPL LABELS FOUND ===")
for k, v in gsheet_ispl_cols.items():
    print(f"{k}: {len(v)} cols defined")

# File role mappings:
# 1. AP Credit Note-C.csv  <->  AP Credit Note-CISPL
# 2. AP Invoice Report-C.csv  <->  AP Invoice Report-C ispl
# 3. BP MASTER-S.csv  <->  ispl BP Master
# 4. Gate Entry Report.csv  <->  Gate Entry Report ispl
# 5. General Ledger.csv  <->  general ledger ispl
# 6. GRPO Report Item Wise.csv  <->  GRPO Report Item Wise ispl
# 7. Item Master ISPL.csv  <->  Item Master ISPL
# 8. Purchase Order Report.csv  <->  Purchase Order Report -ISPL
# 9. Purchase Register Item Wise ISPL-C.csv  <->  Purchase Register Item Wise ISP

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

print("\n\n========================================================")
print("COMPARING GOOGLE SHEET LISTED COLUMNS VS ACTUAL ISPL CSV COLUMNS")
print("========================================================")

for csv_name, gsheet_key in mapping:
    actual_cols = actual_ispl_cols.get(csv_name, [])
    gsheet_cols = gsheet_ispl_cols.get(gsheet_key, [])
    
    actual_set = set(actual_cols)
    gsheet_set = set(gsheet_cols)
    
    in_actual_not_gsheet = [c for c in actual_cols if c not in gsheet_set]
    in_gsheet_not_actual = [c for c in gsheet_cols if c not in actual_set]
    exact_match = (actual_cols == gsheet_cols)
    
    print(f"\n--- {csv_name}  vs  Google Sheet [{gsheet_key}] ---")
    print(f"  Actual CSV Cols Count: {len(actual_cols)} | Google Sheet Listed Cols Count: {len(gsheet_cols)}")
    print(f"  Exact Match: {exact_match}")
    if in_gsheet_not_actual:
        print(f"  [!] In Google Sheet but MISSING in Actual CSV ({len(in_gsheet_not_actual)}):")
        for c in in_gsheet_not_actual:
            print(f"      - {c}")
    else:
        print("  [OK] All Google Sheet columns ARE present in actual CSV file!")
        
    if in_actual_not_gsheet:
        print(f"  [+] In Actual CSV but not listed in Google Sheet row snippet ({len(in_actual_not_gsheet)}):")
        for c in in_actual_not_gsheet[:10]:
            print(f"      + {c}")
        if len(in_actual_not_gsheet) > 10:
            print(f"      ... (+ {len(in_actual_not_gsheet)-10} more)")
