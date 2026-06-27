import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
df_po = pd.read_csv(os.path.join(EXCEL_DIR, "Purchase Order Report-ITL.csv"), dtype=str)

# Search for 252603615
matches = df_po[df_po["PO No"].astype(str).str.contains("252603615")]
print(f"Number of rows with '252603615' in PO No: {len(matches)}")
if not matches.empty:
    print(matches[["PO No", "Vendor Code", "Vendor Name"]].head())
else:
    # Print some close values in PO No
    print("\nSome PO Nos in PO sheet:")
    print(df_po["PO No"].dropna().head(20))
