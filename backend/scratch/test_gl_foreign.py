import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

# Mock the vendor mappings
po_path = os.path.join(cache_dir, "7145fca09fa8c896029d0326324dba61.pkl")
with open(po_path, "rb") as f:
    df_po = pickle.load(f)
po_vendor_info = {}
for idx, row in df_po.iterrows():
    vcode = str(row.get("Vendor Code", "")).strip()
    if vcode:
        curr = str(row.get("Doc Currency", "")).strip()
        vgroup = str(row.get("Vendor Group Name", "")).strip()
        country = "India" if curr.upper() in ("INR", "") else "USA"
        po_vendor_info[vcode] = {'country': country, 'group': vgroup}

gl_rows = df_gl.values.tolist()
current_vendor_code = None
current_vendor_name = None

non_vendor_cats = {'Revenue', 'Asset', 'Equity', 'Expenditure', 'Liability', 'Customer'}

# Keep track of the last transaction row for each vendor
vendor_lasts = {}

for row in gl_rows:
    if not row:
        continue
    val0 = row[0]
    col0_val = str(val0).strip() if (val0 is not None and val0 == val0) else ""
    
    if col0_val == 'Vendor':
        current_vendor_code = str(row[1]).strip() if (row[1] is not None and row[1] == row[1]) else None
        current_vendor_name = str(row[9]).strip() if (len(row) > 9 and row[9] is not None and row[9] == row[9]) else ""
    elif col0_val in non_vendor_cats:
        current_vendor_code = None
        current_vendor_name = None
        
    if not current_vendor_code:
        continue
        
    # Process transactional row
    if not col0_val or col0_val.lower() in ("nan", "none", "vendor"):
        continue
        
    v_info = po_vendor_info.get(current_vendor_code, {})
    country = v_info.get('country', 'India')
    if country == 'India':
        continue
        
    vendor_lasts[current_vendor_code] = row

# Sum the outstanding balances of the last row of each vendor
sum_outstanding = 0.0
for vcode, r in vendor_lasts.items():
    o = float(str(r[13]).replace(",", "").strip()) if (len(r) > 13 and r[13] is not None and str(r[13]).strip() != "") else 0.0
    # Vendor credit balance is negative
    if o < 0:
        sum_outstanding += abs(o)

print(f"Total foreign vendors: {len(vendor_lasts)}")
print(f"Total foreign outstanding: {sum_outstanding:.2f} INR = {sum_outstanding/1e7:.2f} Cr")
