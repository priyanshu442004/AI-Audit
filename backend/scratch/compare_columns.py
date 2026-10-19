import json
import os
import pandas as pd

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\column_analysis.json", "r", encoding="utf-8") as f:
    data = json.load(f)

itl = data["ITL"]
ispl = data["ISPL"]

# File Mappings
# ITL file -> ISPL file
mappings = [
    ("AP Credit Note", "new AP Credit Note-ITL.xls", "AP Credit Note-C.xls"),
    ("BP Master", "BP Master-ITL.xls", "BP MASTER-S.xls"),
    ("Gate Entry Report", "Gate Entry Report ITL.xls", "Gate Entry Report.xls"),
    ("General Ledger", "General Ledger.xls", "General Ledger.xls"),
    ("Item Master", "Item Master-ITL.xls", "Item Master ISPL.xls"),
    ("Purchase Order Report", "Purchase Order Report-ITL.xls", "Purchase Order Report.xls"),
    ("GRPO Report", "new GRPO Report-ITL1.xls", "GRPO Report Item Wise.xls"),
    ("Purchase Register", "Purchase Register Item Wise IKIOTech-C.xls", "Purchase Register Item Wise ISPL-C.xls"),
]

comparison_result = []

for report_name, itl_file, ispl_file in mappings:
    itl_cols = itl.get(itl_file, {}).get("columns", [])
    ispl_cols = ispl.get(ispl_file, {}).get("columns", [])
    
    # Normalize comparison (case-insensitive & stripped)
    itl_cols_clean = [c for c in itl_cols if c and c != '#']
    ispl_cols_clean = [c for c in ispl_cols if c and c != '#']
    
    ispl_cols_lower = set(c.lower() for c in ispl_cols_clean)
    itl_cols_lower = set(c.lower() for c in itl_cols_clean)
    
    missing_in_ispl = [c for c in itl_cols_clean if c.lower() not in ispl_cols_lower]
    missing_in_itl = [c for c in ispl_cols_clean if c.lower() not in itl_cols_lower]
    
    comparison_result.append({
        "report": report_name,
        "itl_file": itl_file,
        "ispl_file": ispl_file,
        "itl_col_count": len(itl_cols_clean),
        "ispl_col_count": len(ispl_cols_clean),
        "itl_columns": itl_cols_clean,
        "ispl_columns": ispl_cols_clean,
        "missing_in_ispl": missing_in_ispl,
        "missing_in_itl": missing_in_itl
    })

# Check extra files in ITL not in ISPL
itl_extra_files = ["AP Invoice Report ITL.xls", "HOLIDAY-2026.xlsx"]

report_data = {
    "comparisons": comparison_result,
    "itl_extra_files": {f: itl[f] for f in itl_extra_files if f in itl}
}

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\detailed_comparison.json", "w", encoding="utf-8") as out:
    json.dump(report_data, out, indent=2, ensure_ascii=False)

print("Saved detailed_comparison.json successfully.")
