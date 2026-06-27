import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
files = os.listdir(EXCEL_DIR)

for f in files:
    if "credit note" in f.lower() and f.endswith(".csv"):
        path = os.path.join(EXCEL_DIR, f)
        print(f"\n--- FILE: {f} ---")
        df = pd.read_csv(path, nrows=5)
        print("Columns:")
        print(df.columns.tolist())
        print("Sample Row 1:")
        print(df.iloc[0].to_dict() if len(df) > 0 else "Empty")
        
    if "grpo" in f.lower() and f.endswith(".csv"):
        path = os.path.join(EXCEL_DIR, f)
        print(f"\n--- FILE: {f} ---")
        df = pd.read_csv(path, nrows=5)
        print("Columns:")
        print(df.columns.tolist())
        print("Sample Row 1:")
        print(df.iloc[0].to_dict() if len(df) > 0 else "Empty")
