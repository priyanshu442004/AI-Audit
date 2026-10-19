import os
import sys
import glob
import asyncio
import pandas as pd
import json

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.pipeline import run_pipeline

ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\p2p newww data\P2P - ISPL & Consumption ITL\P2P - ISPL ( CSV )"

# Mapping ISPL file roles
role_file_map = {
    "ap_credit_note": "AP Credit Note-C.csv",
    "ap_invoice_report": "AP Invoice Report-C.csv",
    "vendor_master": "BP MASTER-S.csv",
    "gate_entry": "Gate Entry Report.csv",
    "general_ledger": "General Ledger.csv",
    "grpo": "GRPO Report Item Wise.csv",
    "item_master": "Item Master ISPL.csv",
    "purchase_order": "Purchase Order Report.csv",
    "purchase_register": "Purchase Register Item Wise ISPL-C.csv",
}

print("=== LOADING ISPL DATAFRAMES ===")
dfs = {}
for role, fname in role_file_map.items():
    fpath = os.path.join(ispl_dir, fname)
    if os.path.exists(fpath):
        try:
            df = pd.read_csv(fpath, encoding='utf-8-sig', low_memory=False)
        except Exception:
            df = pd.read_csv(fpath, encoding='latin1', low_memory=False)
        dfs[role] = df
        print(f"Loaded {role} ({fname}): {len(df)} rows, {len(df.columns)} columns")
    else:
        print(f"MISSING FILE: {role} ({fname})")

print("\n=== RUNNING BACKEND ANALYSIS PIPELINE ON ISPL FILES ===")
async def dummy_emit(stage, pct, msg):
    pass

async def main():
    try:
        results = await run_pipeline(None, dummy_emit, dfs_override=dfs, entity="ISPL", process="P2P")
        print("\n[SUCCESS] PIPELINE EXECUTED SUCCESSFULLY FOR ISPL!")
        print("\nAvailable Result Modules:", list(results.keys()))
        
        # Check Executive summary
        exec_res = results.get("executive", {})
        print("\n--- Executive KPIs ---")
        for k, v in exec_res.get("kpis", {}).items():
            print(f"  - {k}: {v}")
        
        # Check Gate Entry results
        ge_res = results.get("gateentry", {})
        print("\n--- Gate Entry KPIs ---")
        for k, v in ge_res.get("kpis", {}).items():
            print(f"  - {k}: {v}")
            
        if "data" in ge_res:
            print("Gate Entry rows generated:", len(ge_res["data"]))

        # Check Vendor Master results
        vm_res = results.get("vendormaster", {})
        print("\n--- Vendor Master KPIs ---")
        for k, v in vm_res.get("kpis", {}).items():
            print(f"  - {k}: {v}")

        # Check Payment Aging results
        pa_res = results.get("paymentaging", {})
        print("\n--- Payment Aging KPIs ---")
        for k, v in pa_res.get("kpis", {}).items():
            print(f"  - {k}: {v}")

        # Check 3-Way Matching results
        tw_res = results.get("threeway", {})
        print("\n--- 3-Way Matching KPIs ---")
        for k, v in tw_res.get("kpis", {}).items():
            print(f"  - {k}: {v}")

    except Exception as e:
        import traceback
        print("\n[ERROR] RUNNING PIPELINE ON ISPL:")
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
