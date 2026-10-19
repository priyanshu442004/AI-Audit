import os
import glob
import pandas as pd
import json

itl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P New Q2 Data"
ispl_dir = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"

def load_df(filepath):
    if filepath.endswith('.xlsx'):
        try:
            df = pd.read_excel(filepath, nrows=5)
            cols = [str(c).strip().replace('\n', ' ') for c in df.columns]
            return df, cols, "excel_xlsx"
        except Exception as e:
            pass

    for enc in ['utf-16', 'utf-16-le', 'utf-8', 'latin-1', 'cp1252']:
        for sep in [',', '\t', ';']:
            try:
                df = pd.read_csv(filepath, sep=sep, encoding=enc, nrows=5)
                if len(df.columns) > 1:
                    cols = [str(c).strip().replace('\n', ' ') for c in df.columns]
                    cols = [c for c in cols if not c.startswith('Unnamed:')]
                    return df, cols, f"csv({sep}, {enc})"
            except Exception:
                pass

    try:
        df = pd.read_excel(filepath, nrows=5)
        cols = [str(c).strip().replace('\n', ' ') for c in df.columns]
        cols = [c for c in cols if not c.startswith('Unnamed:')]
        return df, cols, "excel_xls"
    except Exception as e:
        return None, [], f"failed: {e}"

def analyze_folder(folder_path):
    results = {}
    for f in sorted(os.listdir(folder_path)):
        full_p = os.path.join(folder_path, f)
        if os.path.isfile(full_p):
            df, cols, fmt = load_df(full_p)
            results[f] = {
                "format": fmt,
                "num_cols": len(cols),
                "columns": cols
            }
    return results

itl_res = analyze_folder(itl_dir)
ispl_res = analyze_folder(ispl_dir)

output_data = {"ITL": itl_res, "ISPL": ispl_res}

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\column_analysis.json", "w", encoding="utf-8") as out:
    json.dump(output_data, out, indent=2, ensure_ascii=False)

print("Saved updated column_analysis.json successfully.")
