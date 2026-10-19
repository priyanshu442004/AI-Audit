import openpyxl
import pandas as pd
import json

filepath = r"C:\Users\hp\Downloads\Purchase Status Report.xlsx"
wb = openpyxl.load_workbook(filepath, data_only=False)
wb_val = openpyxl.load_workbook(filepath, data_only=True)

print("Sheet names:", wb.sheetnames)

for sheetname in wb.sheetnames:
    ws_formula = wb[sheetname]
    ws_value = wb_val[sheetname]
    
    print(f"\n=================== SHEET: {sheetname} ===================")
    print(f"Max row: {ws_formula.max_row}, Max col: {ws_formula.max_column}")
    
    # Read first 50 rows and print non-empty cells
    for r in range(1, min(60, ws_formula.max_row + 1)):
        row_cells = []
        for c in range(1, min(35, ws_formula.max_column + 1)):
            v_form = ws_formula.cell(row=r, column=c).value
            v_val = ws_value.cell(row=r, column=c).value
            if v_form is not None:
                if str(v_form).startswith('='):
                    row_cells.append(f"C{c}[{v_form} => {v_val}]")
                else:
                    row_cells.append(f"C{c}[{v_val}]")
        if row_cells:
            print(f"Row {r:2d}: " + " | ".join(row_cells[:8]))
            if len(row_cells) > 8:
                print(f"        " + " | ".join(row_cells[8:16]))
            if len(row_cells) > 16:
                print(f"        " + " | ".join(row_cells[16:]))
