import os
import pandas as pd

folder = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"
files = [f for f in os.listdir(folder) if f.endswith(('.xls', '.xlsx', '.csv'))]

print(f"Total files: {len(files)}")

for f in sorted(files):
    filepath = os.path.join(folder, f)
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\n==========================================")
    print(f"FILE: {f} ({size_mb:.2f} MB)")
    try:
        # Check engine
        try:
            xl = pd.ExcelFile(filepath)
            sheets = xl.sheet_names
            print(f"Sheets ({len(sheets)}): {sheets}")
            for s in sheets:
                df = xl.parse(s, nrows=5)
                print(f"  Sheet '{s}': Columns count = {len(df.columns)}")
                print(f"  Columns: {df.columns.tolist()}")
        except Exception as ex:
            print(f"Standard pandas excel load failed ({ex}), trying html/csv parser...")
            try:
                dfs = pd.read_html(filepath)
                print(f"Read HTML found {len(dfs)} tables. Table 0 columns: {dfs[0].columns.tolist()}")
            except Exception as ex2:
                print(f"Read HTML also failed: {ex2}")
    except Exception as e:
        print(f"ERROR reading {f}: {e}")
