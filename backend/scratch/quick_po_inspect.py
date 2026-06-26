import os
import pandas as pd

excel_dir = r"C:\Users\hp\Desktop\excel files"
file_mapping = {
    'purchase_order': 'Purchase Order Report-ITL.csv',
    'grpo': 'GRPO Report ITL.csv',
    'ap_invoice_report': 'AP Invoice Report ITL.csv',
    'purchase_register': 'Purchase Register -ITL.csv'
}

for role, filename in file_mapping.items():
    filepath = os.path.join(excel_dir, filename)
    if os.path.exists(filepath):
        print(f"Reading first 5 rows of {filename}...", flush=True)
        df = pd.read_csv(filepath, nrows=5)
        print(f"Columns for {role}: {list(df.columns)}", flush=True)
        # load full df shape
        df_full = pd.read_csv(filepath, usecols=[df.columns[0]])
        print(f"Full row count: {len(df_full)}", flush=True)
    else:
        print(f"File not found: {filename}", flush=True)
