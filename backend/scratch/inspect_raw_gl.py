import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

# Find V01391 vendor section
current_vendor = None
rows_to_print = []
gl_rows = df_gl.values.tolist()
for r in gl_rows:
    if not r:
        continue
    val0 = str(r[0]).strip()
    if val0 == 'Vendor':
        current_vendor = str(r[1]).strip()
    if current_vendor == 'V01391':
        rows_to_print.append(r)
        if len(rows_to_print) >= 20:
            break

print("Raw GL Rows for V01391:")
for r in rows_to_print:
    print(r)
