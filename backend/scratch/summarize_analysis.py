import json

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\column_analysis.json", "r", encoding="utf-8") as f:
    data = json.load(f)

itl = data["ITL"]
ispl = data["ISPL"]

print("=== ITL Files & Column Counts ===")
for fname, info in itl.items():
    print(f"{fname}: {info['num_cols']} cols ({info['format']})")

print("\n=== ISPL Files & Column Counts ===")
for fname, info in ispl.items():
    print(f"{fname}: {info['num_cols']} cols ({info['format']})")
