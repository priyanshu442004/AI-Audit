import json

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\detailed_comparison.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for comp in data["comparisons"]:
    print(f"\n==========================================")
    print(f"REPORT TYPE: {comp['report']}")
    print(f"ITL File:  {comp['itl_file']} ({comp['itl_col_count']} columns)")
    print(f"ISPL File: {comp['ispl_file']} ({comp['ispl_col_count']} columns)")
    print(f"\n--- COLUMNS IN ITL BUT MISSING FROM ISPL ({len(comp['missing_in_ispl'])}) ---")
    for col in comp['missing_in_ispl']:
        print(f"  - {col}")
    print(f"\n--- COLUMNS IN ISPL BUT MISSING FROM ITL ({len(comp['missing_in_itl'])}) ---")
    for col in comp['missing_in_itl']:
        print(f"  - {col}")

print(f"\n==========================================")
print("EXTRA FILES IN ITL NOT PRESENT IN ISPL:")
for fname, info in data["itl_extra_files"].items():
    print(f"\nFile: {fname} ({info['num_cols']} columns)")
    print("Columns:", ", ".join(info['columns']))
