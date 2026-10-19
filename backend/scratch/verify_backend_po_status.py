import sys
backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.analysis import po_status

res = po_status.run({})
print("KPIS RETURNED BY PO_STATUS.PY:")
for k, v in res["kpis"].items():
    print(f"  {k}: {v}")

print("\nTABLE ROWS COUNT:", len(res["tables"][0]["rows"]))
print("TABLE COLUMNS COUNT:", len(res["tables"][0]["columns"]))
print("COLUMNS LIST:")
print(res["tables"][0]["columns"])
