import openpyxl

filepath = r"C:\Users\hp\Downloads\Purchase Status Report.xlsx"
wb_f = openpyxl.load_workbook(filepath, data_only=False)
ws_f = wb_f['Purchase Order Report-ITL']

cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']

for c in cols:
    cell_f = ws_f[f'{c}2']
    v = cell_f.value
    if hasattr(v, 'text'):
        print(f"Cell {c}2 Formula: {v.text}")
    else:
        print(f"Cell {c}2 Formula: {v}")
