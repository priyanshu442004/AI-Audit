import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

# 1. Load BP Master to map BP Code to BP Type
bp_master_path = os.path.join(cache_dir, "76272b21ef204b0de17c1108bc600509.pkl")
with open(bp_master_path, "rb") as f:
    df_bp = pickle.load(f)
bp_types = {str(code).strip(): str(bp_type).strip() for code, bp_type in zip(df_bp["BP Code"], df_bp["BP Type"])}

# 2. Check aging_domestic
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

# Let's filter rows by BP Type == 'S'
filtered_rows = []
for r in rows:
    vcode = r.get("vendor_code")
    bp_type = bp_types.get(vcode)
    if bp_type == 'S':
        filtered_rows.append(r)
        
print(f"Original domestic rows: {len(rows)}")
print(f"Filtered domestic rows (BP Type == 'S'): {len(filtered_rows)}")

# Find unique prefixes in filtered domestic rows
prefixes = {}
for r in filtered_rows:
    doc_no = r.get("invoice_doc_number", "")
    if doc_no and doc_no != "—":
        prefix = doc_no.split()[0] if len(doc_no.split()) > 0 else "None"
        if prefix not in prefixes:
            prefixes[prefix] = 0
        prefixes[prefix] += 1
print("Prefixes in filtered rows:", prefixes)
