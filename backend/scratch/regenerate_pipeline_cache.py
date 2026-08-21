import sys
import pickle
import os

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import load_combined_dfs
from app.analysis import po_status, gate_entry, grn_to_ap, qty_variance, price_variance, gl_balances, payment_aging, msme, vendor_master, item_master, grpo_exceptions, three_way, executive

print("Loading active S3 files via load_combined_dfs(ITL, P2P)...")
dfs = load_combined_dfs(entity="ITL", process="P2P")
print(f"Loaded roles: {list(dfs.keys())}")

print("Running analysis modules on S3 DataFrames...")
po_res = po_status.run(dfs)
ge_res = gate_entry.run(dfs)

cache_dir = os.path.join(backend_dir, ".cache_dfs")
master_cache_path = os.path.join(cache_dir, "pipeline_result.pkl")
itl_cache_path = os.path.join(cache_dir, "pipeline_result_ITL_P2P.pkl")

for path in [master_cache_path, itl_cache_path]:
    data = {}
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
        except Exception as e:
            print(f"Reading existing cache failed: {e}")
    
    data["postatus"] = po_res
    data["gateentry"] = ge_res
    
    try:
        with open(path, "wb") as f:
            pickle.dump(data, f)
        print(f"Successfully updated cache at {path}")
    except Exception as e:
        print(f"Error updating cache at {path}: {e}")

print("Done regenerating pipeline cache using S3 data.")
