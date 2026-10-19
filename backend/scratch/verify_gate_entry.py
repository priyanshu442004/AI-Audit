import sys
backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.analysis import gate_entry

ge_res = gate_entry.run({})
print("KPIS RETURNED BY GATE_ENTRY.PY:")
for k, v in ge_res["kpis"].items():
    print(f"  {k}: {v}")

print("\nTABLES RETURNED:")
for t in ge_res["tables"]:
    print(f"  Title: {t['title']}, Rows: {len(t['rows'])}")
