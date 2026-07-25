import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

gl_rows = df_gl.values.tolist()
current_vendor_code = None
current_vendor_name = None

non_vendor_cats = {'Revenue', 'Asset', 'Equity', 'Expenditure', 'Liability', 'Customer'}

starting_balances = {}

for row in gl_rows:
    if not row:
        continue
    val0 = row[0]
    col0_val = str(val0).strip() if (val0 is not None and val0 == val0) else ""
    
    if col0_val == 'Vendor':
        current_vendor_code = str(row[1]).strip() if (row[1] is not None and row[1] == row[1]) else None
        current_vendor_name = str(row[9]).strip() if (len(row) > 9 and row[9] is not None and row[9] == row[9]) else ""
        starting_bal = float(str(row[13]).replace(",", "").strip()) if (len(row) > 13 and row[13] is not None and str(row[13]).strip() != "") else 0.0
        starting_balances[current_vendor_code] = starting_bal
    elif col0_val in non_vendor_cats:
        current_vendor_code = None
        current_vendor_name = None

# Print top starting balances
non_zero_starts = {k: v for k, v in starting_balances.items() if v != 0}
print(f"Total vendors with non-zero starting balance: {len(non_zero_starts)}")
for k in list(non_zero_starts.keys())[:10]:
    print(f"Vendor: {k}, Starting Balance: {non_zero_starts[k]}")
