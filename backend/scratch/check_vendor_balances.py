import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

# Let's find rows for V00002
gl_rows = df_gl.values.tolist()
current_vendor = None
for r in gl_rows:
    if not r:
        continue
    val0 = str(r[0]).strip()
    if val0 == 'Vendor':
        current_vendor = str(r[1]).strip()
    if current_vendor == 'V00002':
        print(f"DocNo: {r[5]}, Credit: {r[12]}, Debit: {r[11]}, Bal: {r[13]}")
