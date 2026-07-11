import pytest
import pandas as pd
from app.analysis.payment_aging_foreign import run_payment_aging_foreign

def test_payment_aging_foreign_logic():
    # Setup mock data for General Ledger (with custom vendor block rows)
    gl_data = [
        # Vendor header row: Posting Date is "Vendor", second column is cardcode, cardname is in index 9, opening bal in 13
        ["Vendor", "V00002", "", "", "", "", "", "", "", "AR ENTERPRISES", "", "", "", "0.0", "", "", "", ""],
        # Credit transaction (Invoice)
        ["28/01/26", "27/02/26", "22/01/26", "", "IKAP26", "PU 252608814", "1031647", "L-CL-SC-CR-02", "V00002", "A/P Invoices - V00002", "Repair Exp", "", "26322.0", "-26322.0", "", "", "", ""],
        # Debit transaction (Payment)
        ["17/02/26", "17/02/26", "17/02/26", "", "IKAPP26", "PS 252605459", "1031648", "L-CL-SC-CR-02", "V00002", "Outgoing Payment", "Bank", "27212.0", "", "0.0", "", "", "", ""],
        
        # Another Vendor block (International / USA)
        ["Vendor", "V00005", "", "", "", "", "", "", "", "GLOBAL PACKAGING", "", "", "", "0.0", "", "", "", ""],
        ["14/01/26", "13/02/26", "10/01/26", "", "IKAP26", "PU 252608523", "1024386", "L-CL-SC-CR-01", "V00005", "A/P Invoices - V00005", "Clearing", "", "20709.0", "-20709.0", "", "", "", ""]
    ]
    gl_df = pd.DataFrame(gl_data, columns=[
        "Posting Date", "Due Date", "Document Date", "Series (currency)", "Series", "Doc. No.", 
        "Trans. No.", "Control Account", "G/L Acct/BP Code", "Remarks", "Offset Acct Name", 
        "Debit (LC)", "Credit (LC)", "Cumulative Balance (LC)", "Ref. 1 (Header)", "Ref. 1 (Row)", 
        "Remark (Header)", "Remark1 (Header)"
    ])

    # Setup mock PO report (determines country)
    po_df = pd.DataFrame({
        "Vendor Code": ["V00002", "V00005"],
        "Document Currency": ["INR", "USD"],
        "Vendor Group": ["Local Vendor", "Foreign Vendor"]
    })

    # Setup mock BP Master (determines payment terms)
    bp_df = pd.DataFrame({
        "BP Code": ["V00002", "V00005"],
        "Payment Terms Code": ["Net-30", "Net-45"]
    })

    dfs = {
        "general_ledger": gl_df,
        "purchase_order": po_df,
        "vendor_master": bp_df
    }

    result = run_payment_aging_foreign(dfs)
    rows = result["rows"]

    # Only V00005 (Foreign/USD) should be processed, V00002 (INR) should be filtered out
    assert len(rows) == 1
    assert all(r["vendor_code"] == "V00005" for r in rows)

    # Reconciled invoice row checks
    inv_row = rows[0]
    assert inv_row["vendor_name"] == "GLOBAL PACKAGING"
    assert inv_row["vendor_country"] == "USA"
    assert inv_row["vendor_group"] == "Foreign Vendor"
    assert inv_row["payment_terms"] == "Net-45"
    assert inv_row["payment_term_type"] == "Credit(Net)"
    assert inv_row["term_days"] == 45
    assert inv_row["due_date_doc_term"] == "24/02/26" # 10/01/26 + 45 days
    assert inv_row["payment_date"] == "—"
    assert inv_row["days_late"] == 0
    assert inv_row["actual_paid"] == 0.0
    assert inv_row["outstanding"] == 20709.0
    assert inv_row["status"] == "Open"
    assert inv_row["aging_category"] == "Overdue 0-15"
