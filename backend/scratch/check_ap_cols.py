import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
files = os.listdir(EXCEL_DIR)
for f in files:
    if "purchase register" in f.lower() and f.endswith(".csv"):
        path = os.path.join(EXCEL_DIR, f)
        print(f"\n--- FILE: {f} ---")
        df = pd.read_csv(path, nrows=5)
        print(df.columns.tolist())
        print(df.iloc[0].to_dict() if len(df) > 0 else "Empty")
