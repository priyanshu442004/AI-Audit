import pandas as pd
import os

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
cn_path = os.path.join(EXCEL_DIR, "AP Credit Note-ITL.csv")
ap_path = os.path.join(EXCEL_DIR, "Purchase Register -ITL.csv")

df_cn = pd.read_csv(cn_path, dtype=str)
df_ap = pd.read_csv(ap_path, dtype=str)

# Build map from AP's Customer Ref. No. to AP Invoice No
ap_ref_to_inv = {}
for _, row in df_ap.iterrows():
    ref = row.get("Customer Ref. No.")
    inv = row.get("AP Invoice No")
    if pd.notna(ref) and pd.notna(inv):
        ref_norm = str(ref).strip().upper()
        inv_norm = str(inv).strip().upper()
        if ref_norm:
            if ref_norm not in ap_ref_to_inv:
                ap_ref_to_inv[ref_norm] = set()
            ap_ref_to_inv[ref_norm].add(inv_norm)

resolved_count = 0
for idx, row in df_cn.iterrows():
    cn_no = row.get("AP Credit Note No")
    direct_inv = row.get("AP Invoice Number")
    ref = row.get("Vendor Ref No")
    
    invoices = set()
    if pd.notna(direct_inv):
        invoices.add(str(direct_inv).strip().upper())
        
    if pd.notna(ref):
        for r in str(ref).split(","):
            r_norm = str(r).strip().upper()
            if r_norm in ap_ref_to_inv:
                invoices.update(ap_ref_to_inv[r_norm])
                
    if invoices:
        resolved_count += 1
        if idx < 15:
            print(f"CN {cn_no} (Ref: {ref}, Direct: {direct_inv}) -> Invoices: {list(invoices)}")

print(f"\nResolved {resolved_count} out of {len(df_cn)} credit note rows to AP Invoice numbers.")
