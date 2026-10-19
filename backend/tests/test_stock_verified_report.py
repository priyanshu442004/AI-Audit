import io

import pandas as pd

from app.analysis.stock_verified_report import COLUMNS, run_stock_verified_report
from app.loaders import load_file


INV_COLS = [
    "From Date", "To Date", "Item_Code", "Item_Name", "Warehouse_Code", "UOM Name", "ItmsGrpNam",
    "OBQTY", "OBValue", "RecQty(GRPO)", "RecQty(Others)", "RecValue",
    "OutQty(Consumption)", "Out_Qty(Others)", "OutValue", "ClsQty", "ClsValue",
]


def _inv(rows, cols=INV_COLS):
    return pd.DataFrame([dict(zip(cols, r)) for r in rows], dtype=str)


def _pr(rows):
    return pd.DataFrame([{"Document Type": t, "Item Code": c, "Quantity": q} for t, c, q in rows], dtype=str)


D1, D2 = "2026-01-01 00:00:00", "2026-09-30 00:00:00"

INV_ROWS = [
    # From, To, Code, Name, Whs, UOM, Group, OB, OBV, RecGRPO, RecOth, RecV, OutCons, OutOth, OutV, Cls, ClsV
    (D1, D2, "ITEM-A", "Bolt",  "STR-1", "PCS", "RAW MATERIAL",  "10", "0", "100", "5",  "0", "60", "20", "0", "35", "0"),
    (D1, D2, "ITEM-A", "Bolt",  "STR-2", "PCS", "RAW MATERIAL",  "0",  "0", "50",  "0",  "0", "10", "0",  "0", "40", "0"),
    (D1, D2, "900100", "Cap",   "STR-1", "NOS", "FINISHED GOOD", "1",  "0", "0",   "0",  "0", "0",  "0",  "0", "1",  "0"),
    (D1, D2, "ITEM-B", "Nut",   "STR-1", "PCS", "RAW MATERIAL",  "0",  "0", "30",  "0",  "0", "0",  "0",  "0", "30", "0"),
    # closing stock in the report does not agree with the movement
    (D1, D2, "ITEM-C", "Screw", "STR-1", "PCS", "RAW MATERIAL",  "5",  "0", "0",   "0",  "0", "1",  "0",  "0", "3",  "0"),
]

PR_ROWS = [
    ("Purchase Invoice", "ITEM-A", "120"),
    ("Purchase Invoice", "item-a", "40"),        # SUMIF ignores case
    ("Purchase Return",  "ITEM-A", "-10"),       # returns net off
    ("Purchase Invoice", "ITEM-B", "45"),        # more than received in stock -> Remark(PR) Exception
    ("Purchase Invoice", "900100.0", "0"),       # numeric code read back with ".0"
    ("Purchase Invoice", "ITEM-Z", "7"),         # not in the Inventory Report
]


def _run(inv_rows=INV_ROWS, pr_rows=PR_ROWS, inv_cols=INV_COLS):
    dfs = {"inventory_report": _inv(inv_rows, inv_cols)}
    if pr_rows is not None:
        dfs["purchase_register"] = _pr(pr_rows)
    return run_stock_verified_report(dfs)


def _by_code(res):
    return {r["item_code"]: r for r in res["rows"]}


def test_columns_match_excel_layout():
    res = _run()
    assert [c["label"] for c in res["columns"]] == [
        "From Date", "To Date", "Item_Code", "Item_Name", "UOM Name", "ItmsGrpNam", "OBQTY",
        "RecQty PR(GRPO)", "StockQty(GRPO)", "Variation", "Remark(PR)", "RecQty(Others)", "Total RecQty",
        "OutQty(Consumption)", "Out_Qty(Others)", "Total Consume Qty", "ClsQty", "ClsQty(SLR)", "Remark",
    ]
    assert [c["id"] for c in res["columns"]] == [c[0] for c in COLUMNS]


def test_one_row_per_item_in_order_of_first_appearance():
    res = _run()
    assert [r["item_code"] for r in res["rows"]] == ["ITEM-A", "900100", "ITEM-B", "ITEM-C"]
    a = _by_code(res)["ITEM-A"]
    assert a["warehouse_lines"] == 2
    assert (a["from_date"], a["to_date"], a["item_name"], a["uom"], a["item_group"]) == (
        "2026-01-01", "2026-09-30", "Bolt", "PCS", "RAW MATERIAL")


def test_every_formula_column():
    a = _by_code(_run())["ITEM-A"]
    assert a["ob_qty"] == 10                        # G  SUMIF OBQTY
    assert a["pr_rec_qty"] == 150                   # H  120 + 40 - 10
    assert a["stock_rec_qty"] == 150                # I  100 + 50
    assert a["variation"] == 0                      # J  I - H
    assert a["remark_pr"] == "OK"                   # K
    assert a["rec_qty_others"] == 5                 # L
    assert a["total_rec_qty"] == 165                # M  G + I + L
    assert a["out_qty_consumption"] == 70           # N
    assert a["out_qty_others"] == 20                # O
    assert a["total_consume_qty"] == 90             # P  N + O
    assert a["cls_qty"] == 75                       # Q  M - P
    assert a["cls_qty_slr"] == 75                   # R  SUMIF ClsQty
    assert a["remark"] == "OK"                      # S


def test_remark_pr_flags_purchase_register_above_stock_receipt():
    b = _by_code(_run())["ITEM-B"]
    assert b["variation"] == -15
    assert b["remark_pr"] == "Exception"


def test_remark_flags_closing_stock_mismatch():
    res = _run()
    c = _by_code(res)["ITEM-C"]
    assert (c["cls_qty"], c["cls_qty_slr"], c["remark"]) == (4, 3, "Exception")
    assert res["kpis"]["closing_exceptions"] == 1
    assert res["kpis"]["pr_exceptions"] == 1


def test_numeric_codes_match_with_or_without_decimal_suffix():
    cap = _by_code(_run())["900100"]
    assert cap["pr_rec_qty"] == 0 and cap["remark_pr"] == "OK"
    res = _run(pr_rows=[("Purchase Invoice", "900100.0", "3")])
    assert _by_code(res)["900100"]["pr_rec_qty"] == 3


def test_trailing_space_code_is_a_separate_item_like_sumif():
    rows = INV_ROWS + [(D1, D2, "ITEM-B ", "Nut", "STR-9", "PCS", "RAW MATERIAL", "2", "0", "0", "0", "0", "0", "0", "0", "2", "0")]
    res = _run(inv_rows=rows)
    codes = [r["item_code"] for r in res["rows"]]
    assert "ITEM-B" in codes and "ITEM-B " in codes
    spaced = next(r for r in res["rows"] if r["item_code"] == "ITEM-B ")
    assert spaced["pr_rec_qty"] == 0


def test_purchase_register_items_missing_from_inventory_are_reported():
    res = _run()
    assert res["pr_not_in_inventory"] == [{"item_code": "ITEM-Z", "pr_rec_qty": 7}]
    assert res["kpis"]["pr_not_in_inventory"] == 1
    assert any("not in the Inventory Report" in w for w in res["warnings"])


def test_round_half_up_like_excel_in_closing_remark():
    # Q = 1.005 rounds to 1.01 in Excel (Python's round gives 1.0); R = 1.01 -> OK
    rows = [(D1, D2, "ITEM-R", "Ring", "STR-1", "PCS", "RAW MATERIAL", "1.005", "0", "0", "0", "0", "0", "0", "0", "1.01", "0")]
    r = _run(inv_rows=rows, pr_rows=[])["rows"][0]
    assert r["remark"] == "OK"


def test_float_noise_does_not_raise_false_exceptions():
    rows = [
        (D1, D2, "ITEM-F", "Foil", "STR-1", "KG", "RAW MATERIAL", "0", "0", "0.1", "0", "0", "0", "0", "0", "0.1", "0"),
        (D1, D2, "ITEM-F", "Foil", "STR-2", "KG", "RAW MATERIAL", "0", "0", "0.2", "0", "0", "0", "0", "0", "0.2", "0"),
    ]
    r = _run(inv_rows=rows, pr_rows=[("Purchase Invoice", "ITEM-F", "0.3")])["rows"][0]
    assert r["variation"] == 0 and r["remark_pr"] == "OK" and r["remark"] == "OK"


def test_closing_remark_ignores_float_noise_that_excel_flags():
    # Real item RMHWCBXXXX0064: M - P sums to 2320.6149999999907 in binary floats, exactly 2320.615 in decimals
    rows = [
        (D1, D2, "ITEM-H", "Hinge", "HW-STR",  "PCS", "RAW MATERIAL", "8917",     "0", "31299", "0",        "0", "15463.15", "24752.85", "0", "0",        "0"),
        (D1, D2, "ITEM-H", "Hinge", "REJ-STR", "PCS", "RAW MATERIAL", "1.8",      "0", "0",     "0",        "0", "0",        "0",        "0", "1.8",      "0"),
        (D1, D2, "ITEM-H", "Hinge", "EC-STR",  "PCS", "RAW MATERIAL", "3565.655", "0", "23670", "24752.85", "0", "49669.69", "0",        "0", "2318.815", "0"),
        (D1, D2, "ITEM-H", "Hinge", "MFR-WIP", "PCS", "RAW MATERIAL", "0",        "0", "0",     "240",      "0", "240",      "0",        "0", "0",        "0"),
    ]
    r = _run(inv_rows=rows, pr_rows=[])["rows"][0]
    assert (r["cls_qty"], r["cls_qty_slr"], r["remark"]) == (2320.615, 2320.615, "OK")


def test_headers_matched_regardless_of_spelling_order_and_extra_columns():
    cols = ["Extra", "item code", "Item Name", "Rec Qty (GRPO)", "Rec Qty (Others)", "Out Qty (Consumption)",
            "Out Qty (Others)", "Cls Qty", "OB Qty", "From Date", "To Date"]
    rows = [("x", "ITEM-A", "Bolt", "1,000", "0", "400", "0", "650", "50", "01-02-2026", "28-02-2026")]
    res = _run(inv_rows=rows, inv_cols=cols, pr_rows=[("Purchase Invoice", "ITEM-A", "1000")])
    r = res["rows"][0]
    assert (r["stock_rec_qty"], r["total_rec_qty"], r["cls_qty"], r["remark"]) == (1000, 1050, 650, "OK")
    assert (r["from_date"], r["to_date"]) == ("2026-02-01", "2026-02-28")
    assert r["uom"] is None and r["item_group"] is None


def test_blank_and_text_quantities_count_as_zero_and_blank_codes_are_reported():
    rows = INV_ROWS + [
        (D1, D2, "ITEM-B", "Nut", "STR-2", "PCS", "RAW MATERIAL", "", "0", "n/a", "0", "0", "0", "0", "0", "", "0"),
        (D1, D2, "", "Orphan", "STR-2", "PCS", "RAW MATERIAL", "9", "0", "9", "0", "0", "0", "0", "0", "18", "0"),
    ]
    res = _run(inv_rows=rows)
    b = _by_code(res)["ITEM-B"]
    assert b["stock_rec_qty"] == 30 and b["warehouse_lines"] == 2
    assert res["kpis"]["inventory_lines"] == 6
    assert any("no Item_Code" in w for w in res["warnings"])


def test_missing_inventory_report_or_columns_is_an_error():
    assert run_stock_verified_report({})["error"] == "Inventory Report not uploaded."
    res = _run(inv_rows=[("ITEM-A", "1")], inv_cols=["Item_Code", "OBQTY"])
    assert "missing required column" in res["error"] and "ClsQty" in res["error"]


def test_missing_purchase_register_still_builds_report_with_warning():
    res = _run(pr_rows=None)
    assert len(res["rows"]) == 4
    assert all(r["pr_rec_qty"] == 0 for r in res["rows"])
    assert any("Purchase Register not uploaded" in w for w in res["warnings"])


def test_loader_keeps_literal_na_text_for_inventory_report():
    csv = b"Item_Code,Item_Name,OBQTY\nNA,NA,1\nX1,,2\n"
    inv = load_file(io.BytesIO(csv), "inv.csv", role="inventory_report")
    assert inv["Item_Code"].tolist() == ["NA", "X1"]
    assert inv["Item_Name"].tolist()[0] == "NA" and pd.isna(inv["Item_Name"].tolist()[1])
    other = load_file(io.BytesIO(csv), "inv.csv")
    assert pd.isna(other["Item_Code"].tolist()[0])
