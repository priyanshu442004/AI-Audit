import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.loaders import load_file
from app.cleaning import parse_dates

data_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P New Q2 Data"
ge_path = os.path.join(data_dir, "Gate Entry Report ITL.xls")
grpo_path = os.path.join(data_dir, "new GRPO Report-ITL1.xls")

ge_df = load_file(ge_path, "Gate Entry Report ITL.xls")
grpo_df = load_file(grpo_path, "new GRPO Report-ITL1.xls")

ge_df.columns = [str(c).strip() for c in ge_df.columns]
grpo_df.columns = [str(c).strip() for c in grpo_df.columns]

colleague_grpos = [
    "262701034", "262701505", "262701866", "262700297", "262702215",
    "262702245", "262700672", "262701068", "262702244", "262702400",
    "262702402", "262702401", "262700644", "262700716", "262701146",
    "262701297", "262702207"
]

print(f"Colleague provided {len(colleague_grpos)} unique GRPO numbers (list had {20} entries with duplicates).")

# Parse dates
ge_df['GE_Date_dt'] = parse_dates(ge_df['Gate Entry Date'])
ge_df['GRN_Date_dt'] = parse_dates(ge_df['GRN Date'])

ge_df['GRN No. Clean'] = ge_df['GRN No.'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
grpo_df['GRPO No Clean'] = grpo_df['GRPO No'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)

# Inspect colleague's GRPOs in Gate Entry File
ge_colleague = ge_df[ge_df['GRN No. Clean'].isin(colleague_grpos)].copy()
ge_colleague['lag_days'] = (ge_colleague['GRN_Date_dt'] - ge_colleague['GE_Date_dt']).dt.days

print("\n=== COLLEAGUE GRPOS IN GATE ENTRY REPORT ===")
print(f"Found {len(ge_colleague)} rows in Gate Entry file matching colleague's GRPO list.")
print(ge_colleague[['Gate Entry No', 'Gate Entry Date', 'GRN No.', 'GRN Date', 'lag_days']].to_string())

# Inspect colleague's GRPOs in GRPO Report
grpo_colleague = grpo_df[grpo_df['GRPO No Clean'].isin(colleague_grpos)].copy()
grpo_colleague['Posting_Date_dt'] = parse_dates(grpo_colleague['Posting Date'])

# Join with GE Date via Gate Entry No
merged_colleague = pd.merge(
    grpo_colleague,
    ge_df[['Gate Entry No', 'GE_Date_dt']].drop_duplicates(),
    on='Gate Entry No',
    how='left'
)
merged_colleague['lag_posting'] = (merged_colleague['Posting_Date_dt'] - merged_colleague['GE_Date_dt']).dt.days

print("\n=== COLLEAGUE GRPOS MERGED WITH GRPO REPORT ===")
print(f"Found {len(grpo_colleague)} line items in GRPO file for colleague's GRPOs.")
print(merged_colleague[['GRPO No Clean', 'Gate Entry No', 'Posting Date', 'GE_Date_dt', 'lag_posting']].drop_duplicates().to_string())

# Now let's check ALL GRPO Nos in Gate Entry File where lag > 3
ge_df['lag_days'] = (ge_df['GRN_Date_dt'] - ge_df['GE_Date_dt']).dt.days

gt_3_ge = ge_df[ge_df['lag_days'] > 3].copy()
gte_3_ge = ge_df[ge_df['lag_days'] >= 3].copy()

print("\n=== ALL GRPOS IN GATE ENTRY FILE WHERE LAG > 3 DAYS ===")
print(f"Total Rows with lag > 3: {len(gt_3_ge)}")
print(f"Unique GRPO Numbers with lag > 3: {gt_3_ge['GRN No. Clean'].nunique()}")
print("List of Unique GRPO Numbers with lag > 3:")
print(gt_3_ge[['Gate Entry No', 'GRN No. Clean', 'Gate Entry Date', 'GRN Date', 'lag_days']].to_string())

print("\n=== ALL GRPOS IN GATE ENTRY FILE WHERE LAG >= 3 DAYS ===")
print(f"Total Rows with lag >= 3: {len(gte_3_ge)}")
print(f"Unique GRPO Numbers with lag >= 3: {gte_3_ge['GRN No. Clean'].nunique()}")
