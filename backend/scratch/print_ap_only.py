import json

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\detailed_comparison_v2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for comp in data["comparisons"]:
    if comp['report'] == "AP Invoice Report":
        print("=== AP INVOICE REPORT COMPARISON ===")
        print("ITL File:", comp['itl_file'], f"({comp['itl_col_count']} cols)")
        print("ISPL File:", comp['ispl_file'], f"({comp['ispl_col_count']} cols)")
        print("ITL Cols:", comp['itl_columns'])
        print("ISPL Cols:", comp['ispl_columns'])
        print("Missing in ISPL:", comp['missing_in_ispl'])
        print("Missing in ITL:", comp['missing_in_itl'])
