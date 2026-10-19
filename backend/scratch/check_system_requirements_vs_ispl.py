import os
import glob
import re
import pandas as pd

analysis_dir = r"c:\Users\hp\Desktop\Audit\backend\app\analysis"
analysis_files = glob.glob(os.path.join(analysis_dir, "*.py"))

# Helper function to find column names referenced via get_col or column strings
col_pattern = re.compile(r"""['"]([A-Za-z0-9_\. %/\-\#]+)['"]""")

# Load ISPL files and ITL files columns to map
ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\p2p newww data\P2P - ISPL & Consumption ITL\P2P - ISPL ( CSV )"

ispl_files_cols = {}
for filepath in glob.glob(os.path.join(ispl_dir, "*.csv")):
    fname = os.path.basename(filepath)
    df = pd.read_csv(filepath, nrows=1, encoding='utf-8-sig', low_memory=False)
    ispl_files_cols[fname] = list(df.columns)

# Role to filename mapping for ISPL
role_to_ispl_file = {
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

# Detailed examination of each file role
report_lines = []
report_lines.append("=========================================================================")
report_lines.append("DEEP AUDIT REPORT: ISPL FILES vs SYSTEM REQUIREMENTS vs GOOGLE SHEET")
report_lines.append("=========================================================================\n")

for role, ispl_fname in role_to_ispl_file.items():
    cols = ispl_files_cols.get(ispl_fname, [])
    report_lines.append(f"### Role: [{role}] | ISPL File: {ispl_fname} ({len(cols)} columns)")
    report_lines.append(f"Columns present in ISPL CSV:")
    for c in cols:
        report_lines.append(f"  - {c}")
    report_lines.append("\n")

with open('scratch/ispl_deep_report.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print("Wrote base report to scratch/ispl_deep_report.txt")
