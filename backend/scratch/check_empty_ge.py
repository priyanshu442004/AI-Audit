import os
import pandas as pd

path = r"C:\Users\hp\Desktop\excel files\Gate Entry Report-ITL.csv"
df = pd.read_csv(path, dtype=str)

print("Columns:", list(df.columns))
print("Total rows:", len(df))

po_col = "Purchase Order Number"
non_null_po = df[po_col].dropna()
print(f"Non-null rows in {po_col}: {len(non_null_po)}")

# Print value counts of non-null PO numbers
print("\nSample non-null values:")
print(non_null_po.head(10))

# Print count of empty or whitespace values
empty_count = sum(1 for x in df[po_col] if pd.isna(x) or str(x).strip() in ("", "nan", "None", "-"))
print(f"\nEmpty/NaN count in {po_col}: {empty_count}")

# Check first 5 rows specifically
print("\nFirst 5 rows of Gate Entry:")
print(df[[ "Gate Entry No", "Gate Entry Date", po_col ]].head(5))
