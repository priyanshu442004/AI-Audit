import pandas as pd
import glob
import os

folder = r"C:\Users\hp\Desktop\excel files"
csv_files = glob.glob(os.path.join(folder, "*.csv"))

for file_path in csv_files:
    filename = os.path.basename(file_path)
    print("=" * 60)
    print(f"File: {filename}")
    try:
        # read first 5 rows
        df = pd.read_csv(file_path, nrows=5)
        print("Columns:")
        print(list(df.columns))
        print("First row values:")
        if len(df) > 0:
            print(df.iloc[0].to_dict())
    except Exception as e:
        print(f"Error reading {filename}: {e}")
