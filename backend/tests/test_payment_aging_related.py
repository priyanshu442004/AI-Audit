import pytest
import pandas as pd
from app.analysis.payment_aging_related import run_payment_aging_related

def test_payment_aging_related_logic():
    # Setup mock data for General Ledger (with custom vendor block rows)
    gl_data = [
        # Vendor header row: Posting Date is "Vendor", second column is cardcode, cardname is in index 9, opening bal in 13
        ["Vendor", "V00002", "", "", "", "", "", "", "", "AR ENTERPRISES", "", "", "", "0.0", "", "", "", ""],
        # Credit transaction (Invoice)
        ["28/01/26", "27/02/26", "22/01/26", "", "IKAP26", "PU 252608814", "1031647", "L-CL-SC-CR-02", "V00002", "A/P Invoices - V00002", "Repair Exp", "", "26322.0", "-26322.0", "", "", "", ""],
        
        # Another Vendor block (Related Party)
        ["Vendor", "V00005", "", "", "", "", "", "", "", "IKIO SOLUTIONS PVT LTD", "", "", "", "0.0", "", "", "", ""],
        ["14/01/26", "13/02/26", "10/01/26", "", "IKAP26", "PU 252608523", "1024386", "L-CL-SC-CR-01", "V00005", "A/P Invoices - V00005", "Clearing", "", "20709.0", "-20709.0", "", "", "", ""],

        # Another Vendor block (Related Party with different casing and spacing)
        ["Vendor", "V00006", "", "", "", "", "", "", "", " royalux lighting private limited- unit -2  ", "", "", "", "0.0", "", "", "", ""],
        ["14/01/26", "13/02/26", "10/01/26", "", "IKAP26", "PU 252608524", "1024387", "L-CL-SC-CR-01", "V00006", "A/P Invoices - V00006", "Clearing", "", "5000.0", "-5000.0", "", "", "", ""]
    ]
    gl_df = pd.DataFrame(gl_data, columns=[
        "Posting Date", "Due Date", "Document Date", "Series (currency)", "Series", "Doc. No.", 
        "Trans. No.", "Control Account", "G/L Acct/BP Code", "Remarks", "Offset Acct Name", 
        "Debit (LC)", "Credit (LC)", "Cumulative Balance (LC)", "Ref. 1 (Header)", "Ref. 1 (Row)", 
        "Remark (Header)", "Remark1 (Header)"
    ])

    # Setup mock PO report (determines country)
    po_df = pd.DataFrame({
        "Vendor Code": ["V00002", "V00005", "V00006"],
        "Document Currency": ["INR", "INR", "INR"],
        "Vendor Group": ["Local Vendor", "Group Vendor", "Group Vendor"]
    })

    # Setup mock BP Master (determines payment terms)
    bp_df = pd.DataFrame({
        "BP Code": ["V00002", "V00005", "V00006"],
        "Payment Terms Code": ["Net-30", "Net-45", "Net-60"]
    })

    dfs = {
        "general_ledger": gl_df,
        "purchase_order": po_df,
        "vendor_master": bp_df
    }

    result = run_payment_aging_related(dfs)
    rows = result["rows"]

    # V00002 should be filtered out, V00005 and V00006 are related parties and should remain
    assert len(rows) == 2
    vendor_codes = [r["vendor_code"] for r in rows]
    assert "V00002" not in vendor_codes
    assert "V00005" in vendor_codes
    assert "V00006" in vendor_codes

    r1 = next(r for r in rows if r["vendor_code"] == "V00005")
    assert r1["vendor_name"] == "IKIO SOLUTIONS PVT LTD"
    assert r1["payment_terms"] == "Net-45"

    r2 = next(r for r in rows if r["vendor_code"] == "V00006")
    assert r2["vendor_name"] == "royalux lighting private limited- unit -2"
    assert r2["payment_terms"] == "Net-60"
