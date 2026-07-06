import pandas as pd
import os

folder = r"C:\Users\hp\Desktop\excel files"
files = ["AP Credit Note-ITL.csv", "AP Invoice Report ITL.csv", "Purchase Register -ITL.csv"]

for f in files:
    file_path = os.path.join(folder, f)
    if os.path.exists(file_path):
        print("=" * 60)
        print(f"File: {f}")
        try:
            df = pd.read_csv(file_path, nrows=3)
            print("Columns:")
            print(list(df.columns))
            print("First row:")
            print(df.iloc[0].to_dict())
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"File not found: {f}")
