import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

with open(os.path.join(cache_dir, "pipeline_result.pkl"), "rb") as f:
    res = pickle.load(f)

print("Pipeline Result Keys:", list(res.keys()))
print("Executive Keys:", list(res["executive"].keys()) if "executive" in res else None)
if "executive" in res:
    print("Executive KPIs:", res["executive"].get("kpis"))
    print("Executive Charts:", res["executive"].get("charts"))
if "threeway" in res:
    print("Threeway KPIs:", res["threeway"].get("kpis"))
