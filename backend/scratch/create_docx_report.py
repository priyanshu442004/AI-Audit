import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report(output_path):
    doc = docx.Document()
    
    # Page setup - 1 inch margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # Styles Setup
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x2D, 0x37, 0x48) # Dark Slate
    
    # Header Banner
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("ISPL vs ITL P2P Audit Data Gap Analysis")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D) # Navy
    
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(18)
    run_sub = sub_p.add_run("Detailed Review of Missing Analysis Columns in ISPL Data Files (Updated with AP Invoice)")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)
    
    # Executive Summary Box
    summary_table = doc.add_table(rows=1, cols=1)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = summary_table.cell(0, 0)
    set_cell_background(cell, "F7FAFC") # Soft light grey background
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("📌 Executive Summary & Key Updates")
    r.font.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
    
    summary_text = (
        "• AP Invoice Report Added to ISPL: A new file ('AP Invoice Report-C.csv') has been added to ISPL. "
        "It contains 26 columns and is a 100% exact match with ITL's AP Invoice Report, fully resolving the AP Invoice gap.\n"
        "• Holiday Master Excluded: 'HOLIDAY-2026.xlsx' has been excluded from this comparative analysis as requested.\n"
        "• Remaining Data Gaps: Out of 8 active core file pairs reviewed, 5 files still contain missing columns in ISPL "
        "that are present in ITL. The most critical missing columns are the PO Number in GRPO, MSME Registration & PAN No in BP Master, "
        "and Vendor Codes in General Ledger."
    )
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(summary_text)
    r2.font.size = Pt(10.5)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Section 1: Overview Table
    h1 = doc.add_paragraph()
    r = h1.add_run("1. Summary Table of Files Reviewed")
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    h1.paragraph_format.space_after = Pt(8)
    
    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    headers = ["Report Type", "ITL File Name", "ISPL File Name", "Column Status", "Missing Cols in ISPL"]
    widths = [Inches(1.3), Inches(1.6), Inches(1.6), Inches(1.0), Inches(1.0)]
    
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], "2B6CB0") # Blue header
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.runs[0].font.size = Pt(10)
        hdr_cells[i].width = widths[i]
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=100, right=100)

    file_summary_data = [
        ("AP Invoice Report", "AP Invoice Report ITL.xls", "AP Invoice Report-C.csv", "100% Complete", "0 missing"),
        ("Purchase Order Report", "Purchase Order Report-ITL.xls", "Purchase Order Report.xls", "100% Complete", "0 missing"),
        ("AP Credit Note", "new AP Credit Note-ITL.xls", "AP Credit Note-C.xls", "Good (1 Minor)", "1 missing (Remarks)"),
        ("GRPO Report (Goods Receipt)", "new GRPO Report-ITL1.xls", "GRPO Report Item Wise.xls", "Critical Gap", "21 missing"),
        ("BP Master (Vendor Master)", "BP Master-ITL.xls", "BP MASTER-S.xls", "High Gap", "10 missing"),
        ("General Ledger", "General Ledger.xls", "General Ledger.xls", "Medium Gap", "7 missing"),
        ("Item Master", "Item Master-ITL.xls", "Item Master ISPL.xls", "High Gap", "15 missing"),
        ("Gate Entry Report", "Gate Entry Report ITL.xls", "Gate Entry Report.xls", "Minor Gap", "4 missing"),
        ("Purchase Register", "Purchase Register Item Wise...", "Purchase Register Item Wise...", "Complete*", "0 missing (Synonyms)"),
    ]
    
    for row_idx, data_tuple in enumerate(file_summary_data):
        row_cells = table.add_row().cells
        bg_color = "FFFFFF" if row_idx % 2 == 0 else "F7FAFC"
        for col_idx, text in enumerate(data_tuple):
            row_cells[col_idx].text = text
            set_cell_background(row_cells[col_idx], bg_color)
            set_cell_margins(row_cells[col_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[col_idx].paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            row_cells[col_idx].width = widths[col_idx]
            
            # Highlight status
            if "Critical" in text or "High" in text:
                p.runs[0].font.color.rgb = RGBColor(0xC5, 0x30, 0x30) # Red
                p.runs[0].font.bold = True
            elif "100%" in text or "Complete" in text:
                p.runs[0].font.color.rgb = RGBColor(0x2F, 0x85, 0x5A) # Green
                p.runs[0].font.bold = True
                
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 2: Detailed Breakdown File by File
    h2 = doc.add_paragraph()
    r = h2.add_run("2. Detailed Plain-English Breakdown of Missing Columns")
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    h2.paragraph_format.space_after = Pt(8)

    def add_file_detail(title, status_text, desc, missing_list, impact_text):
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(12)
        p_t.paragraph_format.space_after = Pt(4)
        run = p_t.add_run(f"• {title}")
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2B, 0x6C, 0xB0)
        
        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.space_after = Pt(4)
        p_desc.add_run(f"Status: ").bold = True
        p_desc.add_run(f"{status_text}\n")
        p_desc.add_run(f"Overview: ").bold = True
        p_desc.add_run(f"{desc}")
        p_desc.runs[0].font.size = Pt(10.5)
        
        if missing_list:
            p_m = doc.add_paragraph()
            p_m.paragraph_format.space_after = Pt(4)
            p_m.add_run("Columns Available in ITL but Missing from ISPL:").bold = True
            p_m.runs[0].font.size = Pt(10.5)
            
            for item in missing_list:
                p_item = doc.add_paragraph()
                p_item.paragraph_format.left_indent = Inches(0.3)
                p_item.paragraph_format.space_after = Pt(2)
                r_col = p_item.add_run(f"▪ {item['name']}: ")
                r_col.bold = True
                r_col.font.size = Pt(10)
                r_exp = p_item.add_run(item['explain'])
                r_exp.font.size = Pt(10)
                
        p_imp = doc.add_paragraph()
        p_imp.paragraph_format.space_after = Pt(8)
        r_imp_lbl = p_imp.add_run("Audit Impact in Simple Words: ")
        r_imp_lbl.bold = True
        r_imp_lbl.font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
        r_imp_txt = p_imp.add_run(impact_text)
        r_imp_txt.font.size = Pt(10.5)

    # 1. GRPO Report
    add_file_detail(
        title="GRPO Report (Goods Receipt Note / GRN)",
        status_text="High Action Needed (21 Columns Missing in ISPL)",
        desc="This file tracks all physical goods received at the factory warehouse from suppliers.",
        missing_list=[
            {"name": "PO Number", "explain": "The Purchase Order number corresponding to the goods received. Without this, received goods cannot be linked back to the original order."},
            {"name": "Posting Date & Delivery Date", "explain": "The exact dates when the receipt was entered into accounting and physically delivered."},
            {"name": "Series Name & Branch", "explain": "Document numbering series and plant/branch location where goods were delivered."},
            {"name": "Canceled Status", "explain": "Flag indicating if a receipt entry was canceled or reversed."},
            {"name": "Vendor Group Name", "explain": "Supplier category (e.g. Domestic, Import, Raw Material)."},
            {"name": "Document Currency & Document Rate", "explain": "Foreign currency details and exchange rates applied at time of receipt."},
            {"name": "Line Total & Document Total", "explain": "Calculated total financial value of the received items."},
            {"name": "Warehouse Code & Account Code", "explain": "Target warehouse location and General Ledger clearing account."}
        ],
        impact_text="The missing 'PO Number' prevents automated 3-Way Matching (matching PO vs Goods Receipt vs Vendor Invoice). It makes it impossible to automatically verify if suppliers delivered the exact quantities ordered at the agreed PO rates."
    )

    # 2. BP Master
    add_file_detail(
        title="BP Master (Vendor / Supplier Master)",
        status_text="High Action Needed (10 Columns Missing in ISPL)",
        desc="This directory contains master records for all approved suppliers and business partners.",
        missing_list=[
            {"name": "PAN No", "explain": "Permanent Account Number for statutory Income Tax and TDS compliance verification."},
            {"name": "MSME Registration", "explain": "Classification of vendor under MSME Act (Micro, Small, Medium enterprise status)."},
            {"name": "Payment Terms Code", "explain": "Agreed payment terms (e.g. 30 Days, 45 Days, Immediate) used to calculate invoice due dates."},
            {"name": "Active / Inactive Status", "explain": "Flags indicating whether the vendor is currently active or blocked from transactions."},
            {"name": "Creation Date & Date of Update", "explain": "Dates when the vendor was onboarded or modified in ERP."},
            {"name": "Group Name & BP Currency", "explain": "Vendor category and default currency."},
            {"name": "Address Name & Bank Country", "explain": "Primary vendor location name and banking country."}
        ],
        impact_text="Without MSME Registration, the audit system cannot check compliance with the statutory 45-day MSME payment law. Without Payment Terms and PAN No, due dates and tax compliance cannot be validated automatically."
    )

    # 3. General Ledger
    add_file_detail(
        title="General Ledger (Accounting Journal Ledger)",
        status_text="Medium Action Needed (7 Columns Missing in ISPL)",
        desc="This is the complete financial journal recording all accounting transactions and payments.",
        missing_list=[
            {"name": "G/L Acct / BP Code (Vendor Code)", "explain": "Specific Vendor Code (e.g. V000123). ISPL exports general GL account/offset account numbers instead of specific Vendor Codes."},
            {"name": "Control Account", "explain": "Trade Payable GL control account mapping."},
            {"name": "Document Date", "explain": "Original date on the source voucher."},
            {"name": "Ref. 1 (Header) & Ref. 1 (Row)", "explain": "Source voucher reference numbers on header and line level."},
            {"name": "Realization Date & Header Remark", "explain": "Cheque/bank realization date and journal entry explanation text."}
        ],
        impact_text="Because ISPL's GL export lacks the specific Vendor Code column, payment entries and accounting adjustments cannot be directly matched to individual vendor ledgers."
    )

    # 4. Item Master
    add_file_detail(
        title="Item Master (Material Master)",
        status_text="High Action Needed (15 Columns Missing in ISPL)",
        desc="This master file lists all raw materials, components, and items purchased or manufactured.",
        missing_list=[
            {"name": "Preferred Vendor", "explain": "Default supplier assigned for sourcing this material."},
            {"name": "Items per Purchasing / Sales Unit", "explain": "Packaging and Unit of Measure conversion factors (e.g. 1 Box = 50 Pcs)."},
            {"name": "Valuation Method", "explain": "Costing method used for inventory (Moving Average, Standard Cost, FIFO)."},
            {"name": "Active & Inactive Status", "explain": "Flags indicating whether the material is active or discontinued."},
            {"name": "WTax Liable", "explain": "TDS / Withholding Tax applicability flag for the item."},
            {"name": "Group & Subgroup", "explain": "Multi-level material hierarchy categories."},
            {"name": "ItemCodeOld & Service Type", "explain": "Legacy item number mapping and Goods vs Service distinction."},
            {"name": "Approval Status & Production Date", "explain": "Item creation approval state and manufacturing date parameter."}
        ],
        impact_text="Missing valuation methods and preferred vendors limit inventory cost variance analysis. (Note: Additionally, over 70% of active items present in ISPL receipts are missing from the master list itself, requiring a complete fresh export)."
    )

    # 5. Gate Entry Report
    add_file_detail(
        title="Gate Entry Report (Factory Security Log)",
        status_text="Minor Action Needed (4 Columns Missing in ISPL)",
        desc="Log of trucks and physical material entry at the factory security gate.",
        missing_list=[
            {"name": "Vendor Bill No", "explain": "Vendor's delivery bill/invoice number recorded by security guards at entry."},
            {"name": "GRN Gate Entry No & GRN No.", "explain": "Cross-reference link numbers between Gate Entry and warehouse GRN."},
            {"name": "GE Creator ID", "explain": "User ID of the security guard who logged the gate entry."}
        ],
        impact_text="Missing 'Vendor Bill No' prevents direct matching between physical gate entries and vendor invoices at the security stage."
    )

    # 6. AP Credit Note
    add_file_detail(
        title="AP Credit Note (Vendor Credit Memos)",
        status_text="Good Condition (1 Column Missing in ISPL)",
        desc="Records vendor credit notes, price reductions, and returned goods.",
        missing_list=[
            {"name": "Remarks", "explain": "Free-text explanation describing the reason for credit note (e.g. rate difference, damaged goods, return)."}
        ],
        impact_text="Minimal impact. The file is cleanly formatted with complete financial line items."
    )

    # 7. AP Invoice Report
    add_file_detail(
        title="AP Invoice Report (Accounts Payable Invoices)",
        status_text="100% Complete (0 Missing Columns)",
        desc="Comprehensive register of vendor tax invoices entered into accounting.",
        missing_list=[],
        impact_text="No impact! The newly provided 'AP Invoice Report-C.csv' in ISPL matches ITL 100% across all 26 columns, including PO Number, GRPO Number, Vendor Details, and Financial Totals."
    )

    # 8. Purchase Order Report
    add_file_detail(
        title="Purchase Order Report (PO Master)",
        status_text="100% Complete (0 Missing Columns)",
        desc="Official Purchase Orders issued to suppliers containing ordered quantities, rates, and terms.",
        missing_list=[],
        impact_text="No impact! ISPL's Purchase Order file contains all columns present in ITL plus an additional 'Item Sub Group' field."
    )

    # Section 3: Action Plan Checklist for IT / ERP Team
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    h3 = doc.add_paragraph()
    r = h3.add_run("3. Simple Action Checklist for IT / ERP Team")
    r.font.size = Pt(15)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1A, 0x36, 0x5D)
    h3.paragraph_format.space_after = Pt(8)

    p_chk = doc.add_paragraph()
    p_chk.add_run("Please share the following simple checklist with your IT/SAP team to update the export queries:")
    p_chk.paragraph_format.space_after = Pt(8)

    chk_table = doc.add_table(rows=1, cols=3)
    chk_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    chk_headers = ["Target ISPL File", "What to Add / Fix", "Priority"]
    chk_widths = [Inches(2.2), Inches(3.5), Inches(1.3)]
    
    for i, h_text in enumerate(chk_headers):
        cell = chk_table.rows[0].cells[i]
        cell.text = h_text
        set_cell_background(cell, "1A365D")
        p = cell.paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        cell.width = chk_widths[i]
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)

    checklist_items = [
        ("GRPO Report Item Wise.xls", "Add 'PO Number' (Base PO Ref) column into the GRPO export query.", "HIGH"),
        ("BP MASTER-S.xls", "Add 'MSME Registration', 'PAN No', and 'Payment Terms Code' columns.", "HIGH"),
        ("General Ledger.xls", "Include specific 'Vendor Code' (BP Code) alongside GL account numbers.", "MEDIUM"),
        ("Item Master ISPL.xls", "Export a complete, updated Item Master containing all active item codes.", "HIGH"),
        ("Gate Entry Report.xls", "Add 'Vendor Bill No' column to gate entry export.", "MEDIUM"),
        ("AP Credit Note-C.xls", "Add 'Remarks' column to credit note export.", "LOW"),
    ]

    for row_idx, item in enumerate(checklist_items):
        r_cells = chk_table.add_row().cells
        bg = "FFFFFF" if row_idx % 2 == 0 else "F7FAFC"
        for c_idx, val in enumerate(item):
            r_cells[c_idx].text = val
            set_cell_background(r_cells[c_idx], bg)
            set_cell_margins(r_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = r_cells[c_idx].paragraphs[0]
            p.runs[0].font.size = Pt(9.5)
            r_cells[c_idx].width = chk_widths[c_idx]
            if c_idx == 2:
                if val == "HIGH":
                    p.runs[0].font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
                    p.runs[0].font.bold = True
                elif val == "MEDIUM":
                    p.runs[0].font.color.rgb = RGBColor(0xDD, 0x6B, 0x20)
                    p.runs[0].font.bold = True
                else:
                    p.runs[0].font.color.rgb = RGBColor(0x31, 0x97, 0x95)

    doc.save(output_path)
    print(f"Successfully saved docx report to: {output_path}")

# Generate DOCX in both target folders
path1 = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL\ISPL_vs_ITL_Missing_Analysis_Columns_Report.docx"
path2 = r"c:\Users\hp\Desktop\Audit\ISPL_vs_ITL_Missing_Analysis_Columns_Report.docx"

create_report(path1)
create_report(path2)
