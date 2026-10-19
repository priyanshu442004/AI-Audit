import os
import glob
import pandas as pd

itl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P New Q2 Data"
ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"

def get_columns(filepath):
    print(f"\n--- Checking file: {os.path.basename(filepath)} ---")
    file_lower = filepath.lower()
    
    # Try pandas read_excel first
    try:
        df = pd.read_excel(filepath, nrows=5)
        cols = [str(c).strip() for c in df.columns]
        print(f"Read via read_excel. Found {len(cols)} columns.")
        return cols
    except Exception as e:
        print(f"read_excel failed: {e}")
        
    # Try read_html if HTML table masquerading as .xls
    try:
        dfs = pd.read_html(filepath)
        if dfs:
            df = dfs[0]
            cols = [str(c).strip() for c in df.columns]
            print(f"Read via read_html. Found {len(cols)} columns.")
            return cols
    except Exception as e:
        print(f"read_html failed: {e}")
        
    # Try read_csv (tsv/csv)
    for sep in ['\t', ',', ';']:
        try:
            df = pd.read_csv(filepath, sep=sep, nrows=5, encoding_errors='ignore')
            if len(df.columns) > 1:
                cols = [str(c).strip() for c in df.columns]
                print(f"Read via read_csv (sep='{sep}'). Found {len(cols)} columns.")
                return cols
        except Exception as e:
            pass
            
    print("Failed to read file with standard methods.")
    return []

print("=== ITL FILES ===")
itl_files = glob.glob(os.path.join(itl_dir, "*.*"))
itl_headers = {}
for f in itl_files:
    fname = os.path.basename(f)
    itl_headers[fname] = get_columns(f)

print("\n=== ISPL FILES ===")
ispl_files = glob.glob(os.path.join(ispl_dir, "*.*"))
ispl_headers = {}
for f in ispl_files:
    fname = os.path.basename(f)
    ispl_headers[fname] = get_columns(f)
