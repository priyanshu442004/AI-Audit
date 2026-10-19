import json

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\column_analysis.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for category, files in data.items():
    print(f"\n==================== {category} ====================")
    for fname, info in files.items():
        print(f"\n--- File: {fname} ---")
        print(f"Total Columns: {info['num_cols']}")
        print("Columns List:")
        for idx, col in enumerate(info['columns'], 1):
            print(f"  {idx}. {col}")
