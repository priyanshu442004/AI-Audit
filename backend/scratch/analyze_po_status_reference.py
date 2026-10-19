import openpyxl
import pandas as pd
import json

filepath = r"C:\Users\hp\Downloads\Purchase Status Report.xlsx"
wb = openpyxl.load_workbook(filepath, data_only=False)
wb_val = openpyxl.load_workbook(filepath, data_only=True)

out = []

out.append(f"Sheet names: {wb.sheetnames}")

for sheetname in wb.sheetnames:
    ws_form = wb[sheetname]
    ws_val = wb_val[sheetname]
    
    out.append(f"\n========================================================")
    out.append(f"SHEET: {sheetname} (Max row: {ws_form.max_row}, Max col: {ws_form.max_column})")
    out.append(f"========================================================")
    
    # Print first 40 rows
    for r in range(1, min(100, ws_form.max_row + 1)):
        row_str = []
        for c in range(1, min(40, ws_form.max_column + 1)):
            f_val = ws_form.cell(row=r, column=c).value
            v_val = ws_val.cell(row=r, column=c).value
            if f_val is not None:
                cell_name = openpyxl.utils.get_column_letter(c) + str(r)
                if str(f_val).startswith('='):
                    row_str.append(f"{cell_name}: [{f_val} => {v_val}]")
                else:
                    row_str.append(f"{cell_name}: [{v_val}]")
        if row_str:
            out.append(f"Row {r:2d}: " + " | ".join(row_str))

with open('scratch/po_status_reference_summary.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(out))

print("Wrote summary to scratch/po_status_reference_summary.txt")
