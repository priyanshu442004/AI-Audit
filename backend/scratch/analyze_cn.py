import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
cn_path = os.path.join(EXCEL_DIR, "AP Credit Note-ITL.csv")
df_cn = pd.read_csv(cn_path, dtype=str)

print(f"Total AP Credit Note rows: {len(df_cn)}")
print("\nNull AP Invoice Number count:")
print(df_cn["AP Invoice Number"].isna().sum())
print("\nUnique AP Invoice Number values (excluding nan):")
valid_invs = df_cn["AP Invoice Number"].dropna().unique()
print(f"Count of unique valid invoices: {len(valid_invs)}")
print("Sample valid invoices in Credit Note:")
print(valid_invs[:20])

# Let's check if they are comma-separated or have other formats
comma_sep_count = sum(1 for v in valid_invs if "," in v)
print(f"\nNumber of invoice numbers containing commas: {comma_sep_count}")

# Check other columns where AP Invoice number might be stored
print("\nSample rows where AP Invoice Number is NaN:")
nan_rows = df_cn[df_cn["AP Invoice Number"].isna()]
for i, row in nan_rows.head(10).iterrows():
    print(f"Row {i}: Vendor={row['Vendor Code']}, Item={row['Item Code']}, Qty={row['Credit Note Qty']}, Price={row['Credit Note Price']}, Ref={row['Vendor Ref No']}, CN={row['AP Credit Note No']}")
