import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
gl_path = os.path.join(cache_dir, "e3f8150e4b09f608a66240ea00fb6e6e.pkl")
with open(gl_path, "rb") as f:
    df_gl = pickle.load(f)

# Mock the vendor mappings
bp_master_path = os.path.join(cache_dir, "76272b21ef204b0de17c1108bc600509.pkl")
with open(bp_master_path, "rb") as f:
    df_bp = pickle.load(f)
bp_terms = {}
for idx, row in df_bp.iterrows():
    code = str(row.get("BP Code", "")).strip()
    if code:
        bp_terms[code] = str(row.get("Payment Terms Group Name", ""))

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

out_rows = []
gl_rows = df_gl.values.tolist()
current_vendor_code = None
current_vendor_name = None

non_vendor_cats = {'Revenue', 'Asset', 'Equity', 'Expenditure', 'Liability', 'Customer'}

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
        
    # If it is a date, add it
    out_rows.append(row)

print(f"Total rows in Vendor section: {len(out_rows)}")
# Print first 5 rows and their vendor codes
for r in out_rows[:5]:
    print(r[:10])
