"""Tests for Gate Entry Date Integrity module."""

import pytest
import pandas as pd
from app.analysis.gate_entry import run


def test_integrity_high(ge_df, grpo_df):
    result = run(ge_df, grpo_df)
    kpis = result["kpis"]
    # GE003: GE Date 03-01-2026, GRPO Date 02-01-2026 → GE > GRPO (exception)
    assert kpis["exceptions"] >= 1
    assert kpis["integrity_pct"] < 100


def test_no_exceptions():
    """All GE dates before GRPO dates → 100% integrity."""
    ge = pd.DataFrame({
        "Gate Entry No": ["GE001", "GE002"],
        "GRPO No":       ["G001",  "G002"],
        "GE Date":       ["01-01-2026", "01-01-2026"],
    })
    grpo = pd.DataFrame({
        "GRPO No":      ["G001",  "G002"],
        "Posting Date": ["02-01-2026", "03-01-2026"],
    })
    result = run(ge, grpo)
    assert result["kpis"]["exceptions"] == 0
    assert result["kpis"]["integrity_pct"] == 100.0


def test_exception_table_populated(ge_df, grpo_df):
    result = run(ge_df, grpo_df)
    exc_table = next(t for t in result["tables"] if "Exception" in t["title"])
    assert len(exc_table["rows"]) >= 1


def test_charts_structure(ge_df, grpo_df):
    result = run(ge_df, grpo_df)
    pve = result["charts"]["pass_vs_exception"]
    assert "segments" in pve
    assert len(pve["segments"]) == 2


def test_gate_entry_reconciliation_details():
    """Test retrieving details from PO and GRPO reports, handles comma-separated POs and AP Invoices."""
    # 1. Gate Entry sheet has a row with comma-separated PO number
    ge = pd.DataFrame({
        "Gate Entry No": ["GE100"],
        "PO No.":        ["PO100, PO200"],
        "GRPO No":       ["G100"],
        "GE Date":       ["05-01-2026"],
        "Vendor Bill Date": ["01-01-2026"],
    })
    
    # 2. Purchase Order sheet has the item details, quantity, rate, etc.
    po = pd.DataFrame({
        "PO Number": ["PO100", "PO200"],
        "Vendor Code": ["V100", "V100"],
        "Vendor Name": ["Test Vendor", "Test Vendor"],
        "Item Code": ["ITEM_A", "ITEM_B"],
        "Item Description": ["Desc A", "Desc B"],
        "Item Group": ["Group X", "Group X"],
        "Quantity": [10, 20],
        "Price": [100.0, 150.0],
        "Document Rate": [1.0, 1.0],
        "Line Total": [1000.0, 3000.0],
    })

    # 3. GRPO sheet has matching GRPO and base ref (PO)
    grpo = pd.DataFrame({
        "GRPO No": ["G100"],
        "PO Number": ["PO100, PO200"],
        "Document Date": ["06-01-2026"],  # Prioritized document date
        "Posting Date": ["07-01-2026"],
        "Gate Entry No": ["GE100"],
        "Vendor Code": ["V100"],
    })

    # 4. AP Invoice sheet
    ap = pd.DataFrame({
        "AP Invoice No": ["AP999"],
        "PO Number": ["PO100"],
        "GRPO Number": ["G100"],
    })

    dfs = {
        "gate_entry": ge,
        "purchase_order": po,
        "grpo": grpo,
        "ap_invoice_report": ap
    }

    result = run(dfs)
    
    # Get the resulting table
    main_table = next(t for t in result["tables"] if "Full Transaction" in t["title"])
    rows = main_table["rows"]
    
    assert len(rows) == 1
    row = rows[0]
    
    # Check that PO number column handles commas
    assert "PO100" in row["PO Number"]
    assert "PO200" in row["PO Number"]
    
    # Check that item details come from PO report
    assert "ITEM_A" in row["Item Code"]
    assert "ITEM_B" in row["Item Code"]
    assert "Desc A" in row["Item Description"]
    assert "Desc B" in row["Item Description"]
    assert "Group X" in row["Item Group"]
    
    # Check Qty, Rate, Value calculations from PO report
    assert row["Quantity"] == 30.0  # 10 + 20
    assert row["Value(INR)"] == 4000.0 # 1000 + 3000
    assert "100.00" in row["Rate(INR)"]
    assert "150.00" in row["Rate(INR)"]
    
    # Check GRPO date prioritizes Document Date
    assert row["GRPO Date"] == "06/01/26"  # Dayfirst format check
    assert row["Days(GRPO-GE)"] == "1"     # 06/01/26 - 05/01/26 = 1 day
    
    # Check AP Invoice matching
    assert row["AP Invoice Number"] == "AP999"
