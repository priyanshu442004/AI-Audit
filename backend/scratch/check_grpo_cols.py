import os
import pandas as pd

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
df_grpo = pd.read_csv(os.path.join(EXCEL_DIR, "GRPO Report ITL.csv"), nrows=5)
print("GRPO Columns:")
print(list(df_grpo.columns))
