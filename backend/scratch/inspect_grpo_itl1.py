import pandas as pd

f = r"C:\Users\hp\Downloads\GRPO Report-ITL1.xlsx"
try:
    xl = pd.ExcelFile(f)
    print("GRPO Report-ITL1.xlsx sheet names:", xl.sheet_names)
    for s in xl.sheet_names:
        df = pd.read_excel(f, sheet_name=s)
        print(f"\nSheet '{s}' shape:", df.shape)
        print("Columns:", list(df.columns[:10]))
        print("Head:")
        print(df.head(2))
except Exception as e:
    print("Error reading GRPO Report-ITL1.xlsx:", e)
