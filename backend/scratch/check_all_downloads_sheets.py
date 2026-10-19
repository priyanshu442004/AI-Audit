import openpyxl
import os
import glob

downloads_dir = r"C:\Users\hp\Downloads"
excel_files = glob.glob(os.path.join(downloads_dir, "*.xlsx")) + glob.glob(os.path.join(downloads_dir, "*.xls"))

for f in excel_files:
    try:
        wb = openpyxl.load_workbook(f, read_only=True)
        print(f"\nFILE: {os.path.basename(f)}")
        print("Sheets:", wb.sheetnames)
        wb.close()
    except Exception as e:
        print(f"\nFILE: {os.path.basename(f)} - Error: {e}")
