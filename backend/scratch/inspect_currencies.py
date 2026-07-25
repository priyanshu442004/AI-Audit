import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

# Load BP Master
bp_master_path = os.path.join(cache_dir, "76272b21ef204b0de17c1108bc600509.pkl")
with open(bp_master_path, "rb") as f:
    df_bp = pickle.load(f)
print("BP Master Currency value counts:")
if "BP Currency" in df_bp.columns:
    print(df_bp["BP Currency"].value_counts(dropna=False))
else:
    print("BP Currency column not found in BP Master")

# Load PO Report
po_path = os.path.join(cache_dir, "7145fca09fa8c896029d0326324dba61.pkl")
with open(po_path, "rb") as f:
    df_po = pickle.load(f)
print("PO Report Doc Currency value counts:")
if "Doc Currency" in df_po.columns:
    print(df_po["Doc Currency"].value_counts(dropna=False))
elif "Doc. Currency" in df_po.columns:
    print(df_po["Doc. Currency"].value_counts(dropna=False))
else:
    print("Doc Currency/Doc. Currency column not found in PO Report")
    print(list(df_po.columns))
