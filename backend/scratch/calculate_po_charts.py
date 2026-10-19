import sys
import os
import pandas as pd

backend_dir = r"c:\Users\hp\Desktop\Audit\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import load_combined_dfs
from app.analysis import po_status

dfs = load_combined_dfs(entity="ITL", process="P2P")
res = po_status.run(dfs)
rows = res["tables"][0]["rows"]
df = pd.DataFrame(rows)

print("DOCUMENT STATUS COUNTS:")
print(df['Document Status'].value_counts(dropna=False))

total_lines = len(df)
open_lines = len(df[df['Document Status'] == 'Open'])
closed_lines = len(df[df['Document Status'] == 'Closed'])
other_lines = total_lines - (open_lines + closed_lines)

total_val = df['Line Total'].sum()
open_val = df[df['Document Status'] == 'Open']['Line Total'].sum()
closed_val = df[df['Document Status'] == 'Closed']['Line Total'].sum()
other_val = total_val - (open_val + closed_val)

open_line_pct = round((open_lines / total_lines) * 100, 1) if total_lines else 0
closed_line_pct = round((closed_lines / total_lines) * 100, 1) if total_lines else 0

open_val_cr = round(open_val / 1e7, 2)
closed_val_cr = round(closed_val / 1e7, 2)
open_val_pct = round((open_val / total_val) * 100, 1) if total_val else 0
closed_val_pct = round((closed_val / total_val) * 100, 1) if total_val else 0

print("\nMETRICS:")
print(f"Total Lines: {total_lines}")
print(f"Open Lines: {open_lines} ({open_line_pct}%)")
print(f"Closed Lines: {closed_lines} ({closed_line_pct}%)")
print(f"Other Lines: {other_lines}")

print(f"\nTotal Value: {total_val/1e7:.2f} Cr")
print(f"Closed Value: {closed_val_cr:.2f} Cr ({closed_val_pct}%)")
print(f"Open Value: {open_val_cr:.2f} Cr ({open_val_pct}%)")
print(f"Other Value: {other_val/1e7:.2f} Cr")
