import csv

gl_path = r"C:\Users\hp\Desktop\excel files\General Ledger ITL.csv"

print("Reading first 30 rows of GL CSV...")
with open(gl_path, 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if i >= 30:
            break
        print(f"Row {i}: {row}")
