import pickle
import os

cache_path = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs\pipeline_result.pkl"
if os.path.exists(cache_path):
    with open(cache_path, "rb") as f:
        res = pickle.load(f)
    print("Keys of pipeline_result:", res.keys())
    
    # Check executive summary kpis
    exec_res = res.get("executive", {})
    print("Executive keys:", exec_res.keys())
    print("Executive KPIs:")
    for k, v in exec_res.get("kpis", {}).items():
        print(f"  {k}: {v}")
    
    # Check other sections present
    for section in res.keys():
        if section != "executive" and section != "cover":
            print(f"Section {section} keys: {res[section].keys()}")
            print(f"Section {section} KPIs: {res[section].get('kpis', {})}")
else:
    print("pipeline_result.pkl not found!")
