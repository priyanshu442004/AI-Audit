import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
bp_master_path = os.path.join(cache_dir, "76272b21ef204b0de17c1108bc600509.pkl")
with open(bp_master_path, "rb") as f:
    df = pickle.load(f)
print("BP Type value counts:")
print(df["BP Type"].value_counts(dropna=False))
