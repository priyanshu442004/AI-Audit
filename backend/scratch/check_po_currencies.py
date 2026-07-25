import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
po_path = os.path.join(cache_dir, "7145fca09fa8c896029d0326324dba61.pkl")
with open(po_path, "rb") as f:
    df_po = pickle.load(f)
print("PO Report Document Currency value counts:")
print(df_po["Document Currency"].value_counts(dropna=False))
