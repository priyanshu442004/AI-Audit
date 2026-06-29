import pandas as pd
import numpy as np

gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"
print("Reading General Ledger...")

# Let's read the CSV and look at rows with '###'
df_gl = pd.read_csv(gl_path)
print("Columns in GL:", df_gl.columns.tolist())

# Find rows containing '###' in any date column
date_cols = [c for c in df_gl.columns if 'date' in c.lower()]
print("Date columns:", date_cols)

for c in date_cols:
    hashes = df_gl[df_gl[c].astype(str).str.contains('#')]
    if len(hashes) > 0:
        print(f"\nFound {len(hashes)} rows with '#' in column {c}:")
        print(hashes[[df_gl.columns[0], df_gl.columns[1], df_gl.columns[2], 'G/L Acct/BP Code']].head(10).to_string())
