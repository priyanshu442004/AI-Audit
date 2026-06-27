import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
ref_to_search = "BKHW/25-26/9037"

files = os.listdir(EXCEL_DIR)
for f in files:
    if not f.endswith(".csv"):
        continue
    path = os.path.join(EXCEL_DIR, f)
    try:
        df = pd.read_csv(path, dtype=str)
        # Search all columns for the reference string
        for col in df.columns:
            matched = df[df[col].astype(str).str.contains(ref_to_search, na=False, case=False)]
            if not matched.empty:
                print(f"\nFOUND in file: {f}, column: {col}")
                print(matched.head(2).to_dict(orient='records'))
    except Exception as e:
        print(f"Error reading {f}: {e}")
