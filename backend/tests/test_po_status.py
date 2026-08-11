"""Tests for PO Status module."""

import pytest
import pandas as pd
from app.analysis.po_status import run


def test_basic_open_closed(po_df):
    result = run(po_df)
    kpis = result["kpis"]
    # PO003 open_qty=0 → Closed, PO001/ITEM01 open_qty=20 → Open, PO002 all open
    assert kpis["open_lines"] == 2
    assert kpis["closed_lines"] == 2
    assert kpis["total_lines"] == 4
    assert kpis["unique_pos"] == 3


def test_kpi_values(po_df):
    result = run(po_df)
    kpis = result["kpis"]
    # Small test data sums to ~5500 rupees; Cr = /1e7 → may round to 0.0
    # Verify non-negative and open <= total
    assert kpis["open_value_cr"] >= 0
    assert kpis["total_value_cr"] >= kpis["open_value_cr"]
    assert 0 <= kpis["pct_open_value"] <= 100


def test_tables_present(po_df):
    result = run(po_df)
    titles = [t["title"] for t in result["tables"]]
    assert "PO Status Summary" in titles
    assert "Open PO Transaction Data List" in titles


def test_charts_structure(po_df):
    result = run(po_df)
    ps = result["charts"]["po_status"]
    assert "total" in ps
    assert len(ps["segments"]) == 2
    assert ps["segments"][0]["label"] == "Open"
    assert ps["segments"][1]["label"] == "Closed"


def test_all_open(po_df):
    po_df["Open Qty"] = "10"
    result = run(po_df)
    assert result["kpis"]["closed_lines"] == 0
    assert result["kpis"]["open_lines"] == 4


def test_all_closed(po_df):
    po_df["Open Qty"] = "0"
    result = run(po_df)
    assert result["kpis"]["open_lines"] == 0
    assert result["kpis"]["closed_lines"] == 4


def test_cross_file_joins_and_kpis(po_df, grpo_df, pr_df, ge_df):
    # Prepare currency and posting dates in po_df
    po_df["Document currency"] = ["INR", "USD", "INR", "INR"]
    po_df["Document Date"] = ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"]
    po_df["Posting Date"] = ["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04"]
    po_df["Document Status"] = ["OPEN", "OPEN", "Closed", "Closed"]
    po_df["PO Qty"] = ["100", "50", "200", "30"]
    po_df["PO Price"] = ["10.0", "20.0", "10.0", "50.0"]
    po_df["Document Rate"] = ["1.0", "80.0", "1.0", "1.0"]
    po_df["Line Total"] = ["1000.0", "80000.0", "2000.0", "1500.0"]
    po_df["Open Qty"] = ["20", "50", "0", "0"]

    # Align columns in grpo_df
    # PO001/ITEM01 got 80 received
    grpo_df["PO Number"] = grpo_df["Base Ref"]
    grpo_df["Item Code"] = grpo_df["Item No."]
    grpo_df["PO Qty"] = grpo_df["Received Qty"] # alias for received qty
    grpo_df["Posting Date"] = ["2026-03-01", "2026-03-02", "2026-03-03"]

    # Align columns in pr_df (AP Invoice)
    pr_df["PO Number"] = pr_df["PO No"]
    pr_df["GRPO Number"] = ["G001", "G002", "G003", "G004"]
    pr_df["AP Invoice No"] = pr_df["Invoice No"]

    # Gate Entry
    ge_df["Purchase Order Number"] = ["PO001", "PO001", "PO002", "PO003"]
    ge_df["Gate Entry Date"] = ge_df["GE Date"]

    # Combine into dfs dict
    dfs = {
        "purchase_order": po_df,
        "grpo": grpo_df,
        "ap_invoice_report": pr_df,
        "gate_entry": ge_df,
        "holiday": pd.DataFrame({"Date": ["2026-03-01"]}) # March 1 is holiday
    }

    result = run(dfs)
    kpis = result["kpis"]

    # Verify new KPIs
    assert kpis["po_lines"] == 4
    assert kpis["open_lines_pending"] == 2
    assert kpis["po_value_india"] == 4500.0 # PO001 (1000) + PO002 (2000) + PO003 (1500)
    assert kpis["po_value_foreign"] == 80000.0 # PO001/ITEM02 in USD (80000)
    assert kpis["open_po_value"] == 81000.0 # PO001 (1000) + PO001/ITEM02 (80000)
    assert kpis["unique_grn_nos"] == 3 # G001, G002, G003
    assert kpis["unique_ap_invoices"] == 3 # INV001, INV002, INV003

    # Check row-level values in table
    table_rows = result["tables"][3]["rows"]
    assert len(table_rows) == 4

    # PO001 ITEM01
    row0 = table_rows[0]
    assert row0["PO Number"] == "PO001"
    assert row0["Vendor Country"] == "India"
    assert row0["Rate(INR)"] == 10.0
    assert row0["Received Qty."] == 80.0
    assert row0["Pending Qty."] == 20.0
    assert row0["%age Received"] == "80.00%"
    assert row0["Open Value(INR)"] == 200.0
    assert row0["Holiday flag"] == 1 # March 1 is holiday

    # PO001 ITEM02 (USD)
    row1 = table_rows[1]
    assert row1["Vendor Country"] == "USA"
    assert row1["Rate(INR)"] == 1600.0 # 20.0 * 80.0
    assert row1["Holiday flag"] == 0 # March 2 is not holiday (unless weekend)


def test_comma_separated_po_and_variance():
    # Setup DataFrames
    po_data = pd.DataFrame({
        "PO No": ["PO_VAR_1"],
        "Vendor Code": ["V_VAR_1"],
        "Vendor Name": ["Var Vendor"],
        "Item No.": ["ITEM_VAR"],
        "Item Description": ["Var Widget"],
        "Quantity": ["100"],
        "Price": ["10.0"],
        "Open Qty": ["0"],
        "Document currency": ["INR"],
        "Document Date": ["2026-03-01"],
        "Posting Date": ["2026-03-01"],
        "Document Status": ["Closed"],
        "PO Qty": ["100"],
        "PO Price": ["10.0"],
        "Document Rate": ["1.0"],
        "Line Total": ["1000.0"],
    })

    grpo_data = pd.DataFrame({
        "GRPO No": ["G_VAR_1"],
        "PO Number": ["PO_VAR_1"],
        "Item Code": ["ITEM_VAR"],
        "Received Qty": ["110"], # 110 received vs 100 ordered -> variance > 5% is 110 - 105 = 5
        "Rate": ["10.0"],
        "Posting Date": ["2026-03-01"],
        "Gate Entry No": ["GE_VAR_1"],
        "Vendor Code": ["V_VAR_1"],
    })

    # AP Invoice report has comma-separated PO numbers "PO_VAR_1, PO_VAR_OTHER"
    pr_data = pd.DataFrame({
        "Invoice No": ["INV_VAR_1"],
        "PO No": ["PO_VAR_1, PO_VAR_OTHER"],
        "GRPO Number": ["G_VAR_1"],
        "Vendor Code": ["V_VAR_1"],
        "Invoice Date": ["2026-03-05"],
        "Due Date": ["2026-04-05"],
        "Amount": ["1100"],
        "Payment Date": ["2026-03-10"],
    })

    dfs = {
        "purchase_order": po_data,
        "grpo": grpo_data,
        "ap_invoice_report": pr_data,
    }

    result = run(dfs)
    rows = result["tables"][3]["rows"]
    
    assert len(rows) == 1
    row = rows[0]
    
    # Check comma-separated PO AP mapping
    assert row["AP Invoice No."] == "INV_VAR_1"
    
    # Check variance calculation
    # 5% of 100 is 5. Threshold = 105.
    # Received = 110. Variance > 5% = 110 - 105 = 5.
    # Financial difference = 5 * 10 = 50.0.
    assert row["variance>5%"] == 5.0
    assert row["Financial difference"] == 50.0


def test_dynamic_holidays_and_sunday():
    # March 1, 2026 is Sunday
    # March 2, 2026 is Monday (not holiday, not Sunday)
    # March 3, 2026 is Tuesday (we will put it in holiday list)
    po_data = pd.DataFrame({
        "PO No": ["PO_HOL_1", "PO_HOL_2", "PO_HOL_3"],
        "Vendor Code": ["V_VAR_1", "V_VAR_1", "V_VAR_1"],
        "Vendor Name": ["Var Vendor", "Var Vendor", "Var Vendor"],
        "Item No.": ["ITEM_VAR", "ITEM_VAR", "ITEM_VAR"],
        "Item Description": ["Var Widget", "Var Widget", "Var Widget"],
        "Quantity": ["100", "100", "100"],
        "Price": ["10.0", "10.0", "10.0"],
        "Open Qty": ["0", "0", "0"],
        "Document currency": ["INR", "INR", "INR"],
        "Document Date": ["2026-03-01", "2026-03-02", "2026-03-03"],
        "Posting Date": ["2026-03-01", "2026-03-02", "2026-03-03"],
        "Document Status": ["Closed", "Closed", "Closed"],
        "PO Qty": ["100", "100", "100"],
        "PO Price": ["10.0", "10.0", "10.0"],
        "Document Rate": ["1.0", "1.0", "1.0"],
        "Line Total": ["1000.0", "1000.0", "1000.0"],
    })

    dfs = {
        "purchase_order": po_data,
        "holiday": pd.DataFrame({"Date": ["2026-03-03"]}) # March 3 is holiday
    }

    result = run(dfs)
    rows = result["tables"][3]["rows"]

    assert len(rows) == 3
    # Row 0: March 1, 2026 (Sunday) -> Holiday flag = 1, Holiday Name = Sunday
    assert rows[0]["Holiday flag"] == 1
    assert rows[0]["Holiday Name"] == "Sunday"
    # Row 1: March 2, 2026 (Monday, not holiday) -> Holiday flag = 0, Holiday Name = none
    assert rows[1]["Holiday flag"] == 0
    assert rows[1]["Holiday Name"] == "none"
    # Row 2: March 3, 2026 (Tuesday, holiday) -> Holiday flag = 1, Holiday Name = Public Holiday
    assert rows[2]["Holiday flag"] == 1
    assert rows[2]["Holiday Name"] == "Public Holiday"


