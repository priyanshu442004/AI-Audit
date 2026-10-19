import pypdf

pdf_path = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL\ISPL_P2P_Audit_File_Issues_Report.pdf"

reader = pypdf.PdfReader(pdf_path)
print(f"Num pages: {len(reader.pages)}")
full_text = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    full_text.append(f"--- PAGE {i+1} ---\n" + text)

with open(r"c:\Users\hp\Desktop\Audit\backend\scratch\pdf_text.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(full_text))

print("Saved pdf_text.txt successfully.")
