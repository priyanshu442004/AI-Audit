import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Page numbering canvas
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header banner text (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "ISPL P2P Audit — File Review & Action Plan Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(54, 742, 558, 742)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL — For Internal & Management Review Only")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 48, 558, 48)
        
        self.restoreState()


def generate_pdf(output_paths):
    doc_margin = 54 # 0.75 in
    
    for out_path in output_paths:
        doc = SimpleDocTemplate(
            out_path,
            pagesize=letter,
            leftMargin=doc_margin,
            rightMargin=doc_margin,
            topMargin=doc_margin + 10,
            bottomMargin=doc_margin
        )
        
        styles = getSampleStyleSheet()
        
        # Custom Paragraph Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0284C7"),
            spaceAfter=15
        )
        
        section_heading = ParagraphStyle(
            'SecHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6
        )
        
        body_bold = ParagraphStyle(
            'BodyDarkBold',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        card_title = ParagraphStyle(
            'CardTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0F172A")
        )

        badge_red = ParagraphStyle(
            'BadgeRed',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#DC2626")
        )

        badge_orange = ParagraphStyle(
            'BadgeOrange',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#D97706")
        )

        badge_green = ParagraphStyle(
            'BadgeGreen',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#16A34A")
        )

        table_header = ParagraphStyle(
            'TblHdr',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        table_cell = ParagraphStyle(
            'TblCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B")
        )

        table_cell_bold = ParagraphStyle(
            'TblCellBold',
            parent=table_cell,
            fontName='Helvetica-Bold'
        )

        story = []

        # Document Header Banner Card
        header_data = [
            [
                Paragraph("<b>ISPL P2P AUDIT — DATA QUALITY & FILE HEALTH REVIEW</b>", title_style),
            ],
            [
                Paragraph("<b>Target Entity:</b> ISPL | <b>Process:</b> Procure-to-Pay (P2P) Audit | <b>Files Reviewed:</b> 8 Data Files", subtitle_style)
            ],
            [
                Paragraph(
                    "This report summarizes the data health check conducted on the 8 Excel files provided for ISPL's P2P Audit. "
                    "It highlights what each file is used for, what specific issues were found in simple language, what impact "
                    "these issues cause in the audit, and the exact action required from your IT / ERP team.",
                    body_style
                )
            ]
        ]
        header_table = Table(header_data, colWidths=[504])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('PADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 0),
            ('TOPPADDING', (0,1), (-1,1), 0),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 14))

        # Executive Summary Table
        story.append(Paragraph("1. Executive Summary Table", section_heading))
        
        summary_rows = [
            [
                Paragraph("File Name", table_header),
                Paragraph("Audit Role", table_header),
                Paragraph("Status", table_header),
                Paragraph("Main Issue Identified", table_header),
                Paragraph("Action Needed", table_header),
            ],
            [
                Paragraph("<b>Item Master ISPL.xls</b>", table_cell),
                Paragraph("Item Master", table_cell),
                Paragraph("<b>🔴 High Issue</b>", badge_red),
                Paragraph("Over 70% of active bought items are missing from this master list.", table_cell),
                Paragraph("Provide full updated Item Master export.", table_cell),
            ],
            [
                Paragraph("<b>GRPO Report Item Wise.xls</b>", table_cell),
                Paragraph("Goods Receipt (GRN)", table_cell),
                Paragraph("<b>🔴 High Issue</b>", badge_red),
                Paragraph("Missing 'Purchase Order No' (PO No) column.", table_cell),
                Paragraph("Add PO No column to GRPO export query.", table_cell),
            ],
            [
                Paragraph("<b>Purchase Register ISPL-C.xls</b>", table_cell),
                Paragraph("Purchase Invoices", table_cell),
                Paragraph("<b>🔴 High Issue</b>", badge_red),
                Paragraph("Missing 'Purchase Order No' (PO No) column.", table_cell),
                Paragraph("Add PO No column to Purchase Register export.", table_cell),
            ],
            [
                Paragraph("<b>BP MASTER-S.xls</b>", table_cell),
                Paragraph("Vendor Master", table_cell),
                Paragraph("<b>🟠 Medium Issue</b>", badge_orange),
                Paragraph("Missing MSME classification; Vendor V000128 missing.", table_cell),
                Paragraph("Add MSME category & missing vendor to BP Master.", table_cell),
            ],
            [
                Paragraph("<b>Gate Entry Report.xls</b>", table_cell),
                Paragraph("Security Gate Log", table_cell),
                Paragraph("<b>🟠 Medium Issue</b>", badge_orange),
                Paragraph("Missing Bill Date; 222 PO numbers not found in PO Report.", table_cell),
                Paragraph("Add Bill Date & verify 222 PO numbers.", table_cell),
            ],
            [
                Paragraph("<b>General Ledger.xls</b>", table_cell),
                Paragraph("GL Journal", table_cell),
                Paragraph("<b>🟠 Medium Issue</b>", badge_orange),
                Paragraph("Missing Vendor Code column (uses GL Offset Account).", table_cell),
                Paragraph("Include Vendor Code in GL export.", table_cell),
            ],
            [
                Paragraph("<b>Purchase Order Report.xls</b>", table_cell),
                Paragraph("PO Details", table_cell),
                Paragraph("<b>🟢 Good</b>", badge_green),
                Paragraph("Clean formatting and complete data (1,649 POs).", table_cell),
                Paragraph("None (Ready for use).", table_cell),
            ],
            [
                Paragraph("<b>AP Credit Note-C.xls</b>", table_cell),
                Paragraph("Credit Memos", table_cell),
                Paragraph("<b>🟢 Good</b>", badge_green),
                Paragraph("Clean formatting and complete line data (613 rows).", table_cell),
                Paragraph("None (Ready for use).", table_cell),
            ],
        ]

        summary_table = Table(summary_rows, colWidths=[110, 75, 75, 140, 104])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 14))

        # Section 2: Detailed File Review
        story.append(Paragraph("2. Detailed File Analysis & Audit Impact", section_heading))

        def make_file_card(title, role, status_badge, purpose, problem, impact, action):
            content = [
                [
                    Paragraph(f"<b>{title}</b> &nbsp;&nbsp;|&nbsp;&nbsp;<font color='#64748B'>Role: {role}</font>", card_title),
                    Paragraph(status_badge, ParagraphStyle('RRight', parent=styles['Normal'], alignment=2))
                ],
                [
                    Paragraph(f"<b>What this file is for:</b> {purpose}", body_style),
                    Paragraph("", body_style)
                ],
                [
                    Paragraph(f"<b><font color='#DC2626'>The Problem Found:</font></b> {problem}", body_style),
                    Paragraph("", body_style)
                ],
                [
                    Paragraph(f"<b><font color='#475569'>What it Causes in Audit:</font></b> {impact}", body_style),
                    Paragraph("", body_style)
                ],
                [
                    Paragraph(f"<b><font color='#0284C7'>Action Required:</font></b> {action}", body_style),
                    Paragraph("", body_style)
                ]
            ]
            t = Table(content, colWidths=[380, 124])
            t.setStyle(TableStyle([
                ('SPAN', (0,1), (1,1)),
                ('SPAN', (0,2), (1,2)),
                ('SPAN', (0,3), (1,3)),
                ('SPAN', (0,4), (1,4)),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
                ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor("#E2E8F0")),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,0), 4),
            ]))
            return t

        # File 1: Item Master
        c1 = make_file_card(
            title="1. Item Master ISPL.xls",
            role="Material & Item Master",
            status_badge="<font color='#DC2626'><b>🔴 HIGH IMPACT</b></font>",
            purpose="List of all raw materials, components, and items purchased or manufactured.",
            problem="<b>Severe Missing Data:</b> Over 70% of active items present in purchase receipts (GRPO) are missing from this master list. Out of 3,773 item codes in GRPO, 2,701 items do not exist in this file.",
            impact="The audit system cannot verify item descriptions, standard unit prices, or categories for missing items. Quantity and rate variance reports will flag these items as 'Unregistered Master Items'.",
            action="Request your IT/SAP team to download a complete, updated export of the Item Master containing all currently active item codes."
        )
        story.append(c1)
        story.append(Spacer(1, 10))

        # File 2: GRPO Report
        c2 = make_file_card(
            title="2. GRPO Report Item Wise.xls",
            role="Goods Receipt (GRN)",
            status_badge="<font color='#DC2626'><b>🔴 HIGH IMPACT</b></font>",
            purpose="Record of all physical goods received and accepted at the factory warehouse.",
            problem="<b>Missing Column:</b> The 'Purchase Order Number' (PO No) column is missing from this file export.",
            impact="The system cannot directly link received goods back to their original Purchase Order numbers. 3-Way Matching (PO vs Goods Receipt vs Invoice) cannot automatically verify if correct PO quantities were received.",
            action="Ask your IT team to include the <b>'PO No' (or Base PO Ref)</b> column in the GRPO report export query."
        )
        story.append(c2)
        story.append(Spacer(1, 10))

        # File 3: Purchase Register
        c3 = make_file_card(
            title="3. Purchase Register Item Wise ISPL-C.xls",
            role="Purchase Invoices",
            status_badge="<font color='#DC2626'><b>🔴 HIGH IMPACT</b></font>",
            purpose="Complete register of vendor tax invoices entered into accounting.",
            problem="<b>Missing Column:</b> The 'Purchase Order Number' (PO No) column is missing from this register.",
            impact="Invoice line items cannot be automatically cross-matched to originating PO numbers, making it difficult to detect over-billing against PO price limits.",
            action="Ask your IT team to add the <b>'PO No'</b> column into the Purchase Register export query."
        )
        story.append(c3)
        story.append(Spacer(1, 10))

        # File 4: BP Master
        c4 = make_file_card(
            title="4. BP MASTER-S.xls",
            role="Vendor Master",
            status_badge="<font color='#D97706'><b>🟠 MEDIUM IMPACT</b></font>",
            purpose="Directory of all approved suppliers, vendors, and business partners.",
            problem="<b>Missing MSME Field & Vendor Code:</b> No MSME / Udyam registration classification column (Micro, Small, Medium, Non-MSME) is provided. Additionally, active vendor <b>V000128</b> is missing from this file.",
            impact="The system cannot automatically classify vendors under the legal <b>45-day MSME payment rule</b>. Transactions for vendor V000128 will show as 'Unregistered Vendor'.",
            action="Provide an updated Vendor Master file that includes the <b>MSME Category</b> column and includes vendor V000128."
        )
        story.append(c4)
        story.append(Spacer(1, 10))

        # File 5: Gate Entry Report
        c5 = make_file_card(
            title="5. Gate Entry Report.xls",
            role="Security Gate Entry Log",
            status_badge="<font color='#D97706'><b>🟠 MEDIUM IMPACT</b></font>",
            purpose="Record of physical trucks and material inward entries logged at factory security gates.",
            problem="<b>Missing Bill Date & Unmatched POs:</b> Lacks Vendor Bill Date column. Furthermore, 222 PO numbers referenced at the gate (e.g. PO #13267, #13054) do not exist in the Purchase Order Report file.",
            impact="Cannot calculate exact delivery delay between Vendor Invoice Date and Gate Entry Date. Gate entries for those 222 POs cannot be verified against official POs.",
            action="Ask IT to include 'Vendor Bill Date' in the gate entry export, and check if those 222 POs belong to another branch or series."
        )
        story.append(c5)
        story.append(Spacer(1, 10))

        # File 6: General Ledger
        c6 = make_file_card(
            title="6. General Ledger.xls",
            role="Accounting Journal Ledger",
            status_badge="<font color='#D97706'><b>🟠 MEDIUM IMPACT</b></font>",
            purpose="Detailed financial transaction journal showing all account entries and payments.",
            problem="<b>Missing Vendor Code Column:</b> The file exports GL Offset Account numbers instead of specific Vendor Codes (V000xxx). Headers use 'Debit (LC)' and 'Credit (LC)'.",
            impact="Payment aging and vendor ledger reconciliation cannot map accounting entries directly to individual vendor codes.",
            action="Ensure GL export query includes the <b>Vendor Code (BP Code)</b> column alongside general ledger account numbers."
        )
        story.append(c6)
        story.append(Spacer(1, 10))

        # File 7: Purchase Order Report
        c7 = make_file_card(
            title="7. Purchase Order Report.xls",
            role="PO Header & Line Items",
            status_badge="<font color='#16A34A'><b>🟢 GOOD CONDITION</b></font>",
            purpose="Official Purchase Orders issued to vendors containing ordered quantities, rates, and terms.",
            problem="<b>No Issues Found:</b> File is cleanly structured with 6,869 rows and 1,649 unique PO numbers. All key columns are 100% complete.",
            impact="None. File is ready for full audit processing.",
            action="No action required for this file."
        )
        story.append(c7)
        story.append(Spacer(1, 10))

        # File 8: AP Credit Note
        c8 = make_file_card(
            title="8. AP Credit Note-C.xls",
            role="Credit Notes & Adjustments",
            status_badge="<font color='#16A34A'><b>🟢 GOOD CONDITION</b></font>",
            purpose="Record of vendor credit notes, price deductions, and returned goods.",
            problem="<b>No Issues Found:</b> File is cleanly structured with 613 rows. All required line fields are present.",
            impact="None. File is ready for full audit processing.",
            action="No action required for this file."
        )
        story.append(c8)
        story.append(Spacer(1, 14))

        # Section 3: Summary Action Checklist for Client's IT Team
        story.append(KeepTogether([
            Paragraph("3. Quick Action Checklist for IT / SAP Team", section_heading),
            Paragraph(
                "Please share the following checklist with your IT / ERP team so they can re-export the files with the missing columns:",
                body_style
            ),
            Spacer(1, 6),
            Table([
                [Paragraph("Item #", table_header), Paragraph("Target File", table_header), Paragraph("Exact Action Required from IT Team", table_header)],
                [Paragraph("1", table_cell_bold), Paragraph("Item Master ISPL.xls", table_cell), Paragraph("Export a complete Item Master containing all active item codes (currently >70% of active items are missing).", table_cell)],
                [Paragraph("2", table_cell_bold), Paragraph("GRPO Report Item Wise.xls", table_cell), Paragraph("Add the <b>PO No</b> (or Base PO Ref) column into the GRPO report export.", table_cell)],
                [Paragraph("3", table_cell_bold), Paragraph("Purchase Register ISPL-C.xls", table_cell), Paragraph("Add the <b>PO No</b> column into the Purchase Register export.", table_cell)],
                [Paragraph("4", table_cell_bold), Paragraph("BP MASTER-S.xls", table_cell), Paragraph("Add the <b>MSME Category</b> column (Micro / Small / Medium / Non-MSME) and include vendor <b>V000128</b>.", table_cell)],
                [Paragraph("5", table_cell_bold), Paragraph("Gate Entry Report.xls", table_cell), Paragraph("Add <b>Vendor Bill Date</b> column, and verify the 222 missing PO numbers.", table_cell)],
                [Paragraph("6", table_cell_bold), Paragraph("General Ledger.xls", table_cell), Paragraph("Include the <b>Vendor Code (BP Code)</b> column alongside account numbers.", table_cell)],
            ], colWidths=[40, 160, 304], style=[
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284C7")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('PADDING', (0,0), (-1,-1), 5),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ])
        ]))

        doc.build(story, canvasmaker=NumberedCanvas)
        print(f"PDF successfully generated at: {out_path}")

if __name__ == "__main__":
    out_dir1 = r"C:\Users\hp\Documents\SQL Server Management Studio\P2P - ISPL"
    out_file1 = os.path.join(out_dir1, "ISPL_P2P_Audit_File_Issues_Report.pdf")
    
    out_dir2 = r"C:\Users\hp\Desktop\Audit"
    out_file2 = os.path.join(out_dir2, "ISPL_P2P_Audit_File_Issues_Report.pdf")
    
    generate_pdf([out_file1, out_file2])
