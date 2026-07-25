import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"
with open(os.path.join(cache_dir, "aging_domestic.pkl"), "rb") as f:
    data = pickle.load(f)
rows = data.get("rows", [])

# Find unique prefixes in invoice_doc_number
prefixes = {}
for r in rows:
    doc_no = r.get("invoice_doc_number", "")
    if doc_no and doc_no != "—":
        prefix = doc_no.split()[0] if len(doc_no.split()) > 0 else "None"
        if prefix not in prefixes:
            prefixes[prefix] = {"count": 0, "sum_out": 0.0, "sum_abs_out": 0.0}
        o = float(r.get("outstanding") or 0.0)
        prefixes[prefix]["count"] += 1
        prefixes[prefix]["sum_out"] += o
        prefixes[prefix]["sum_abs_out"] += abs(o)

print("Document prefixes in domestic aging:")
for p, stats in prefixes.items():
    print(f"  Prefix: {p}, Count: {stats['count']}, Net Out: {stats['sum_out']:.2f}, Abs Out: {stats['sum_abs_out']:.2f}")
