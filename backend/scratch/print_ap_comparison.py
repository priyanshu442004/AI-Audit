import json

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\detailed_comparison_v2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for comp in data["comparisons"]:
    print(f"\n==========================================")
    print(f"REPORT TYPE: {comp['report']}")
    print(f"ITL File:  {comp['itl_file']} ({comp['itl_col_count']} columns)")
    print(f"ISPL File: {comp['ispl_file']} ({comp['ispl_col_count']} columns)")
    print(f"ITL Cols:  {comp['itl_columns']}")
    print(f"ISPL Cols: {comp['ispl_columns']}")
    print(f"\n--- COLUMNS IN ITL BUT MISSING FROM ISPL ({len(comp['missing_in_ispl'])}) ---")
    for col in comp['missing_in_ispl']:
        print(f"  - {col}")
