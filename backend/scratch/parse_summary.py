import openpyxl
import pandas as pd
import json

filepath = r"C:\Users\hp\Downloads\Purchase Status Report.xlsx"
wb_form = openpyxl.load_workbook(filepath, data_only=False)
wb_val = openpyxl.load_workbook(filepath, data_only=True)

print("=== SHEETS IN REFERENCE WORKBOOK ===")
for sheet in wb_form.sheetnames:
    print(" -", sheet)

ws_f = wb_form.worksheets[0]
ws_v = wb_val.worksheets[0]

print(f"\n=== FIRST SHEET: {ws_f.title} ===")

# Search for KPI blocks or table headers
headers = []
for col in range(1, ws_f.max_column + 1):
    val = ws_v.cell(row=42, column=col).value # Row 42 was where table headers started in previous trace, or let's search for header row
    headers.append((col, openpyxl.utils.get_column_letter(col), val))

# Find row where table headers start (contains 'PO No' or 'Item Code' or 'Vendor Name')
header_row = None
for r in range(1, 100):
    row_vals = [str(ws_v.cell(row=r, column=c).value).strip() for c in range(1, ws_v.max_column + 1)]
    if 'PO No' in row_vals or 'Vendor Name' in row_vals or 'PO Status' in row_vals:
        header_row = r
        break

print(f"Header Row found at Row {header_row}:")
cols_list = []
for c in range(1, ws_f.max_column + 1):
    c_name = ws_v.cell(row=header_row, column=c).value
    if c_name is not None:
        c_letter = openpyxl.utils.get_column_letter(c)
        sample_formula = ws_f.cell(row=header_row+1, column=c).value
        sample_value = ws_v.cell(row=header_row+1, column=c).value
        cols_list.append({
            "col_idx": c,
            "col_letter": c_letter,
            "col_name": str(c_name).strip(),
            "sample_formula": str(sample_formula) if str(sample_formula).startswith('=') else None,
            "sample_value": str(sample_value)
        })

print(f"\nTOTAL COLUMNS IN TABLE: {len(cols_list)}")
for col in cols_list:
    print(f"Col {col['col_idx']:2d} ({col['col_letter']}): '{col['col_name']}' | Formula: {col['sample_formula']} | Sample: {col['sample_value']}")

# Now let's find KPI cards (rows 1 to header_row-1)
print(f"\n=== KPI CARDS & SUMMARY TABLES ABOVE HEADER ROW (Rows 1 to {header_row-1}) ===")
for r in range(1, header_row):
    row_cells = []
    for c in range(1, ws_f.max_column + 1):
        vf = ws_f.cell(row=r, column=c).value
        vv = ws_v.cell(row=r, column=c).value
        if vf is not None:
            c_let = openpyxl.utils.get_column_letter(c)
            row_cells.append(f"{c_let}{r}: '{vf}' [Val: {vv}]")
    if row_cells:
        print(f"Row {r:2d}: " + " | ".join(row_cells))
