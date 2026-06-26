import pandas as pd
import os

po_path = r"C:\Users\hp\Desktop\excel files\Purchase Order Report-ITL.csv"
grpo_path = r"C:\Users\hp\Desktop\excel files\GRPO Report ITL.csv"

print("PO Columns:")
df_po = pd.read_csv(po_path, nrows=5)
print(list(df_po.columns))

print("\nGRPO Columns:")
df_grpo = pd.read_csv(grpo_path, nrows=5)
print(list(df_grpo.columns))
