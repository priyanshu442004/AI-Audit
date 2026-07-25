import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

gl_rows = df_gl.values.tolist()
first_col_values = set()
for r in gl_rows:
    if r and not r[0] != r[0]: # not NaN
        val = str(r[0]).strip()
        # If it's not a date, let's keep it
        if val and not any(char.isdigit() for char in val):
            first_col_values.add(val)

print("Unique non-date values in first column of GL:")
print(first_col_values)
