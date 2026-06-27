import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"

cn_path = os.path.join(EXCEL_DIR, "AP Credit Note-ITL.csv")
ap_path = os.path.join(EXCEL_DIR, "Purchase Register -ITL.csv")

df_cn = pd.read_csv(cn_path, dtype=str)
df_ap = pd.read_csv(ap_path, dtype=str)

print("Columns in Credit Note:", df_cn.columns.tolist())
print("Columns in AP Invoice:", df_ap.columns.tolist())

# Normalize function
def normalize(s):
    if pd.isna(s):
        return ""
    return str(s).strip().upper()

# Check overlap of Vendor Ref No in CN with Customer Ref. No. in AP
cn_refs = set()
for ref in df_cn["Vendor Ref No"].dropna():
    for r in str(ref).split(","):
        normalized = normalize(r)
        if normalized and len(normalized) > 3:
            cn_refs.add(normalized)

ap_refs = set(df_ap["Customer Ref. No."].dropna().apply(normalize))

overlap = cn_refs.intersection(ap_refs)
print(f"\nNumber of CN Vendor Ref Nos: {len(cn_refs)}")
print(f"Number of AP Customer Ref. Nos: {len(ap_refs)}")
print(f"Number of matches between CN 'Vendor Ref No' and AP 'Customer Ref. No.': {len(overlap)}")
print("Sample matches:", list(overlap)[:10])
