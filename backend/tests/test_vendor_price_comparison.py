import pandas as pd

from app.analysis.vendor_price_comparison import (
    DIFFERENT_VENDOR_COLUMNS,
    SAME_VENDOR_COLUMNS,
    run_vendor_price_comparison,
)


def _po(rows):
    cols = [
        "Numerator", "PO No", "Posting Date", "Document Status", "Canceled Status",
        "Vendor Group", "Vendor Code", "Vendor Name", "Item Code", "Item Description",
        "UOM", "PO Qty", "PO Price", "Document Currency", "Document Rate", "Line Total", "Open Qty",
    ]
    return pd.DataFrame([dict(zip(cols, r)) for r in rows], dtype=str)


LOCAL, INTER, GROUP, FOREIGN = "Local Vendor", "Inter State Vendor", "Group Company Vendor", "Foreign vendor"

PO_ROWS = [
    # Numerator, PO No, Posting Date, Status, Canceled, Vendor Group, Vendor, Name, Item, Desc, UOM, Qty, Price, Cur, Rate, Line, Open
    ("1", "101", "2026-01-05 00:00:00", "Closed", "No", LOCAL,   "V1", "Alpha", "ITEM-A", "Bolt", "PCS", "10", "5",   "INR", "1", "50",  "0"),
    ("2", "102", "2026-02-05 00:00:00", "Closed", "No", LOCAL,   "V1", "Alpha", "ITEM-A", "Bolt", "PCS", "10", "5.5", "INR", "1", "55",  "0"),
    ("3", "103", "2026-03-05 00:00:00", "Closed", "No", LOCAL,   "V1", "Alpha", "ITEM-A", "Bolt", "PCS", "20", "5.5", "INR", "1", "110", "0"),
    ("4", "104", "2026-01-20 00:00:00", "Closed", "No", INTER,   "V2", "Beta",  "ITEM-A", "Bolt", "PCS", "30", "4.9", "INR", "1", "147", "0"),
    ("5", "105", "2026-04-01 00:00:00", "OPEN",   "No", INTER,   "V3", "Gamma", "ITEM-A", "Bolt", "PCS", "5",  "6",   "INR", "1", "30",  "5"),
    # item bought once only -> never in Same Vendor
    ("6", "106", "2026-01-10 00:00:00", "Closed", "No", LOCAL,   "V1", "Alpha", "ITEM-B", "Nut",  "PCS", "1",  "2",   "INR", "1", "2",   "0"),
    # numeric item code bought twice by the same vendor
    ("7", "107", "2026-01-11 00:00:00", "Closed", "No", LOCAL,   "V4", "Delta", "900100", "Cap",  "NOS", "1",  "3",   "INR", "1", "3",   "0"),
    ("8", "108", "2026-02-11 00:00:00", "Closed", "No", LOCAL,   "V4", "Delta", "900100", "Cap",  "NOS", "1",  "3.2", "INR", "1", "3.2", "0"),
    # excluded lines: group company, foreign, USD, canceled
    ("9",  "109", "2026-01-12 00:00:00", "Closed", "No",  GROUP,   "V5", "Sister", "ITEM-A", "Bolt", "PCS", "1", "4",   "INR", "1",  "4",   "0"),
    ("10", "110", "2026-01-13 00:00:00", "Closed", "No",  FOREIGN, "V6", "Import", "ITEM-A", "Bolt", "PCS", "1", "4.1", "INR", "1",  "4.1", "0"),
    ("11", "111", "2026-01-14 00:00:00", "Closed", "No",  INTER,   "V7", "Dollar", "ITEM-A", "Bolt", "PCS", "1", "0.1", "USD", "90", "0.1", "0"),
    ("12", "112", "2026-01-15 00:00:00", "Closed", "Yes", LOCAL,   "V8", "Gone",   "ITEM-A", "Bolt", "PCS", "1", "4.2", "INR", "1",  "4.2", "0"),
]


def _run():
    return run_vendor_price_comparison({"purchase_order": _po(PO_ROWS)})


def test_columns_match_excel_layout():
    res = _run()
    assert [c["id"] for c in res["same_vendor"]["columns"]] == SAME_VENDOR_COLUMNS
    assert [c["id"] for c in res["different_vendor"]["columns"]] == DIFFERENT_VENDOR_COLUMNS
    labels = [c["label"] for c in res["same_vendor"]["columns"]]
    assert labels[11] == "Duplicate Vendor Code" and labels[20] == "Price Key"


def test_same_vendor_rows_and_helper_columns():
    rows = _run()["same_vendor"]["rows"]
    # numeric item codes sort before text codes, then by posting date; OPEN / excluded lines dropped,
    # duplicate Price Key (ITEM-A-5.5 on PO 103) removed, single-line ITEM-B dropped
    assert [(r["po_no"], r["price_key"]) for r in rows] == [
        ("107", "900100-3"),
        ("108", "900100-3.2"),
        ("101", "ITEM-A-5"),
        ("104", "ITEM-A-4.9"),
        ("102", "ITEM-A-5.5"),
    ]
    by_po = {r["po_no"]: r for r in rows}
    assert by_po["101"]["duplicate_vendor_code"] == "YES"
    assert by_po["104"]["duplicate_vendor_code"] == "NO"
    assert all(r["duplicate_item_code"] == "YES" for r in rows)
    assert by_po["101"]["posting_date"] == "2026-01-05"
    assert by_po["104"]["po_price"] == 4.9 and by_po["104"]["line_total"] == 147.0


def test_different_vendor_rows_and_helper_columns():
    rows = _run()["different_vendor"]["rows"]
    # ITEM-A is the only item bought from 2+ vendors; one line per vendor (first by posting date),
    # OPEN status is allowed here; excluded vendor groups / currency / canceled are not
    assert [(r["po_no"], r["key"], r["price_key"]) for r in rows] == [
        ("101", "V1-ITEM-A", "ITEM-A-5"),
        ("104", "V2-ITEM-A", "ITEM-A-4.9"),
        ("105", "V3-ITEM-A", "ITEM-A-6"),
    ]
    assert all(r["duplicate_item_code"] == "YES" for r in rows)
    assert rows[2]["document_status"] == "OPEN"


def test_different_vendor_drops_repeated_price_key_across_vendors():
    extra = list(PO_ROWS) + [
        ("13", "113", "2026-05-01 00:00:00", "Closed", "No", LOCAL, "V9", "Epsilon", "ITEM-A", "Bolt", "PCS", "1", "5", "INR", "1", "5", "0"),
    ]
    rows = run_vendor_price_comparison({"purchase_order": _po(extra)})["different_vendor"]["rows"]
    assert "V9-ITEM-A" not in [r["key"] for r in rows]  # same price as V1's line already kept


def test_missing_po_or_columns_returns_error():
    assert run_vendor_price_comparison({})["error"]
    res = run_vendor_price_comparison({"purchase_order": pd.DataFrame({"Vendor Code": ["V1"], "PO Price": ["1"]})})
    assert "Item Code" in res["error"]
    assert res["same_vendor"]["rows"] == [] and res["different_vendor"]["rows"] == []
