import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
cn_path = os.path.join(EXCEL_DIR, "AP Credit Note-ITL.csv")
po_path = os.path.join(EXCEL_DIR, "Purchase Order Report-ITL.csv")

df_cn = pd.read_csv(cn_path, dtype=str)
df_po = pd.read_csv(po_path, dtype=str)

# Normalize function
def normalize(s):
    if pd.isna(s) or s is None:
        return ""
    val_str = str(s).strip().upper()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

cn_pairs = set()
for _, row in df_cn.iterrows():
    vc = normalize(row.get("Vendor Code"))
    ic = normalize(row.get("Item Code"))
    if vc and ic:
        cn_pairs.add((vc, ic))

po_pairs = set()
for _, row in df_po.iterrows():
    vc = normalize(row.get("Vendor Code"))
    ic = normalize(row.get("Item Code"))
    if vc and ic:
        po_pairs.add((vc, ic))

overlap = cn_pairs.intersection(po_pairs)
print(f"Unique (Vendor Code, Item Code) in Credit Notes: {len(cn_pairs)}")
print(f"Unique (Vendor Code, Item Code) in PO: {len(po_pairs)}")
print(f"Matches: {len(overlap)}")
