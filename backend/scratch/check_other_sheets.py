import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"

df_grpo = pd.read_csv(os.path.join(EXCEL_DIR, "GRPO Report ITL.csv"), dtype=str)
df_ap = pd.read_csv(os.path.join(EXCEL_DIR, "AP Invoice Report ITL.csv"), dtype=str)

# Test PO: 252603615
po = "252603615"

grpo_matches = df_grpo[df_grpo["PO Number"].astype(str).str.contains(po)]
print(f"GRPO matches for PO {po}: {len(grpo_matches)}")
if not grpo_matches.empty:
    print(grpo_matches[["GRPO No", "PO Number", "Gate Entry No", "Posting Date"]].head())

ap_matches = df_ap[df_ap["PO Number"].astype(str).str.contains(po)]
print(f"AP Invoice matches for PO {po}: {len(ap_matches)}")
if not ap_matches.empty:
    print(ap_matches[["AP Invoice No", "PO Number", "GRPO Number"]].head())
