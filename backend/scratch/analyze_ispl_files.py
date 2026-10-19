import os
import glob
import pandas as pd
import csv
import json

ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\p2p newww data\P2P - ISPL & Consumption ITL\P2P - ISPL ( CSV )"

# 1. Read headers of all 9 ISPL CSV files
ispl_files_info = {}
for filepath in glob.glob(os.path.join(ispl_dir, "*.csv")):
    filename = os.path.basename(filepath)
    try:
        df = pd.read_csv(filepath, nrows=2, encoding='utf-8-sig', low_memory=False)
        cols = list(df.columns)
    except Exception as e:
        try:
            df = pd.read_csv(filepath, nrows=2, encoding='latin1', low_memory=False)
            cols = list(df.columns)
        except Exception as e2:
            cols = [f"Error loading: {e2}"]
    ispl_files_info[filename] = cols

print("=== ISPL CSV FILES & THEIR COLUMNS ===")
for fname, cols in ispl_files_info.items():
    print(f"\n--- File: {fname} ({len(cols)} columns) ---")
    for c in cols:
        print("  -", repr(c))

# 2. Read raw gsheet lines
with open('scratch/gsheet_raw.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    gsheet_rows = list(reader)

print("\n=== GOOGLE SHEET CONTENTS ===")
for idx, r in enumerate(gsheet_rows):
    non_empty = [c for c in r if c.strip()]
    if non_empty:
        print(f"Row {idx}: {non_empty[:15]}")
