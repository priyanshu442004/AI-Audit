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

# Clean column names
ge_df.columns = [str(c).strip() for c in ge_df.columns]
grpo_df.columns = [str(c).strip() for c in grpo_df.columns]

# Parse dates in Gate Entry
ge_df['GE_Date_dt'] = parse_dates(ge_df['Gate Entry Date'])
ge_df['GRN_Date_dt'] = parse_dates(ge_df['GRN Date'])

print("=== ANALYSIS 1: INSIDE GATE ENTRY REPORT ALONE ===")
print(f"Total Gate Entry Rows: {len(ge_df)}")
print(f"Gate Entry Rows with valid GE Date: {ge_df['GE_Date_dt'].notna().sum()}")
print(f"Gate Entry Rows with valid GRN Date: {ge_df['GRN_Date_dt'].notna().sum()}")

ge_with_dates = ge_df[ge_df['GE_Date_dt'].notna() & ge_df['GRN_Date_dt'].notna()].copy()
ge_with_dates['lag_days'] = (ge_with_dates['GRN_Date_dt'] - ge_with_dates['GE_Date_dt']).dt.days

print(f"\nWithin Gate Entry File (Raw Row Level):")
print(f" 1. Strict GRN Date > GE Date + 3 days (lag > 3): {(ge_with_dates['lag_days'] > 3).sum()}")
print(f" 2. GRN Date >= GE Date + 3 days (lag >= 3): {(ge_with_dates['lag_days'] >= 3).sum()}")
print(f" 3. Positive lag within window (0 to 3 days): {((ge_with_dates['lag_days'] >= 0) & (ge_with_dates['lag_days'] <= 3)).sum()}")
print(f" 4. Negative lag (GE Date > GRN Date): {(ge_with_dates['lag_days'] < 0).sum()}")

# Unique GE No level in GE File
ge_unique = ge_with_dates.groupby('Gate Entry No')['lag_days'].max().reset_index()
print(f"\nUnique Gate Entry Number Level (In Gate Entry File):")
print(f" - Unique Gate Entry Nos where max lag > 3 days: {(ge_unique['lag_days'] > 3).sum()}")
print(f" - Unique Gate Entry Nos where max lag >= 3 days: {(ge_unique['lag_days'] >= 3).sum()}")

print("\n=== ANALYSIS 2: JOINING GATE ENTRY WITH GRPO REPORT ===")
# Parse GRPO Posting Date & Document Date
grpo_df['Posting_Date_dt'] = parse_dates(grpo_df['Posting Date'])
grpo_df['Doc_Date_dt'] = parse_dates(grpo_df['Document Date'])

# Merge on Gate Entry No
merged = pd.merge(
    ge_df[['Gate Entry No', 'GE_Date_dt']].dropna(subset=['Gate Entry No']),
    grpo_df[['Gate Entry No', 'Posting_Date_dt', 'Doc_Date_dt', 'GRPO No', 'PO Number']].dropna(subset=['Gate Entry No']),
    on='Gate Entry No',
    how='inner'
)
print(f"Merged GRPO-GE Line Items: {len(merged)}")
merged['lag_posting'] = (merged['Posting_Date_dt'] - merged['GE_Date_dt']).dt.days
merged['lag_doc'] = (merged['Doc_Date_dt'] - merged['GE_Date_dt']).dt.days

print(f"\nUsing GRPO Posting Date (Line Item Level):")
print(f" - Total Line Items where Posting Date > GE Date + 3 days (lag > 3): {(merged['lag_posting'] > 3).sum()}")
print(f" - Total Line Items where Posting Date >= GE Date + 3 days (lag >= 3): {(merged['lag_posting'] >= 3).sum()}")

# Group by Gate Entry No: Earliest Posting Date
ge_earliest = merged.groupby('Gate Entry No')['lag_posting'].min().reset_index()
print(f"\nUnique Gate Entry Nos (Using Earliest GRPO Date):")
print(f" - Unique Gate Entry Nos where Earliest Posting Date > GE Date + 3 days: {(ge_earliest['lag_posting'] > 3).sum()}")
print(f" - Unique Gate Entry Nos where Earliest Posting Date >= GE Date + 3 days: {(ge_earliest['lag_posting'] >= 3).sum()}")

# Group by Gate Entry No: Latest Posting Date
ge_latest = merged.groupby('Gate Entry No')['lag_posting'].max().reset_index()
print(f"\nUnique Gate Entry Nos (Using Latest GRPO Date):")
print(f" - Unique Gate Entry Nos where Latest Posting Date > GE Date + 3 days: {(ge_latest['lag_posting'] > 3).sum()}")
print(f" - Unique Gate Entry Nos where Latest Posting Date >= GE Date + 3 days: {(ge_latest['lag_posting'] >= 3).sum()}")

# Working Days calculation (excluding Saturdays & Sundays)
print("\n=== ANALYSIS 3: WORKING DAYS (EXCLUDING WEEKENDS) ===")
def calc_bday(row):
    start = row['GE_Date_dt']
    end = row['GRN_Date_dt']
    if pd.isna(start) or pd.isna(end):
        return np.nan
    if end >= start:
        return len(pd.bdate_range(start, end)) - 1
    else:
        return - (len(pd.bdate_range(end, start)) - 1)

ge_with_dates['bday_lag'] = ge_with_dates.apply(calc_bday, axis=1)
print(f"Within Gate Entry File (Working Days):")
print(f" - Rows where Working Days > 3 days: {(ge_with_dates['bday_lag'] > 3).sum()}")
print(f" - Rows where Working Days >= 3 days: {(ge_with_dates['bday_lag'] >= 3).sum()}")

print("\n=== SUMMARY DISTRIBUTION OF CALENDAR DAYS (GRN Date - GE Date) ===")
print(ge_with_dates['lag_days'].value_counts().sort_index())
