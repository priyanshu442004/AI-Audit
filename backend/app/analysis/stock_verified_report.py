"""
Stock Verified Report — built from the Inventory Report, checked against the Purchase Register.

Reproduces the auditor's Excel workings (Sheet1 of "Stock Verified Report.xlsx"):
one line per distinct Item_Code of the Inventory Report (in order of first appearance),
with From Date / To Date / Item_Name / UOM Name / ItmsGrpNam taken from that first line.

Per item (SUMIF over every warehouse line of the item):
    G  OBQTY                = SUMIF(Inventory Item_Code, item, OBQTY)
    H  RecQty PR(GRPO)      = SUMIF(Purchase Register Item Code, item, Quantity)
    I  StockQty(GRPO)       = SUMIF(Inventory Item_Code, item, RecQty(GRPO))
    J  Variation            = I - H
    K  Remark(PR)           = "Exception" if J < 0 else "OK"
    L  RecQty(Others)       = SUMIF(Inventory Item_Code, item, RecQty(Others))
    M  Total RecQty         = G + I + L
    N  OutQty(Consumption)  = SUMIF(Inventory Item_Code, item, OutQty(Consumption))
    O  Out_Qty(Others)      = SUMIF(Inventory Item_Code, item, Out_Qty(Others))
    P  Total Consume Qty    = N + O
    Q  ClsQty               = M - P
    R  ClsQty(SLR)          = SUMIF(Inventory Item_Code, item, ClsQty)
    S  Remark               = "OK" if ROUND(Q, 2) = ROUND(R, 2) else "Exception"

Item codes are matched the way SUMIF matches them: case-insensitive, numbers and
numeric text alike, but otherwise exact — a code with a trailing space is its own item.
The Purchase Register is summed over all of its lines, so Purchase Returns (negative
quantities) net off Purchase Invoices.

Two deliberate differences from the Excel sheet:
  * its Remark(PR) formula points two rows up (=IF(J2<0,...) on row 4); this module
    applies the intended same-row check;
  * quantities are cleaned of binary floating-point noise before Remark compares them,
    so a ClsQty that is 2320.615 exactly is not flagged against a ClsQty(SLR) of 2320.615
    the way Excel's 2320.6149999999907 is.
"""

from __future__ import annotations

import math
import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


# (id, label, aliases) — aliases are compared with headers lower-cased and stripped of
# everything but letters and digits, so "RecQty(GRPO)", "Rec Qty GRPO" and "recqty_grpo" all match
INVENTORY_FIELDS = [
    ("from_date",           "From Date",           ["fromdate"]),
    ("to_date",             "To Date",             ["todate"]),
    ("item_code",           "Item_Code",           ["itemcode", "itemno"]),
    ("item_name",           "Item_Name",           ["itemname", "itemdescription"]),
    ("uom",                 "UOM Name",            ["uomname", "uom"]),
    ("item_group",          "ItmsGrpNam",          ["itmsgrpnam", "itemgroupname", "itemgroup"]),
    ("ob_qty",              "OBQTY",               ["obqty", "openingqty"]),
    ("rec_qty_grpo",        "RecQty(GRPO)",        ["recqtygrpo"]),
    ("rec_qty_others",      "RecQty(Others)",      ["recqtyothers"]),
    ("out_qty_consumption", "OutQty(Consumption)", ["outqtyconsumption"]),
    ("out_qty_others",      "Out_Qty(Others)",     ["outqtyothers"]),
    ("cls_qty",             "ClsQty",              ["clsqty", "closingqty"]),
]
INVENTORY_LABEL = {f[0]: f[1] for f in INVENTORY_FIELDS}
INVENTORY_QTY_FIELDS = ["ob_qty", "rec_qty_grpo", "rec_qty_others", "out_qty_consumption", "out_qty_others", "cls_qty"]

PR_FIELDS = [
    ("item_code", "Item Code", ["itemcode", "itemno"]),
    ("quantity",  "Quantity",  ["quantity", "qty"]),
]
PR_LABEL = {f[0]: f[1] for f in PR_FIELDS}

# (id, label, type, computed) — column layout exactly as in the Excel sheet
COLUMNS = [
    ("from_date",           "From Date",           "date", False),
    ("to_date",             "To Date",             "date", False),
    ("item_code",           "Item_Code",           "id",   False),
    ("item_name",           "Item_Name",           "text", False),
    ("uom",                 "UOM Name",            "text", False),
    ("item_group",          "ItmsGrpNam",          "text", False),
    ("ob_qty",              "OBQTY",               "num",  True),
    ("pr_rec_qty",          "RecQty PR(GRPO)",     "num",  True),
    ("stock_rec_qty",       "StockQty(GRPO)",      "num",  True),
    ("variation",           "Variation",           "num",  True),
    ("remark_pr",           "Remark(PR)",          "text", True),
    ("rec_qty_others",      "RecQty(Others)",      "num",  True),
    ("total_rec_qty",       "Total RecQty",        "num",  True),
    ("out_qty_consumption", "OutQty(Consumption)", "num",  True),
    ("out_qty_others",      "Out_Qty(Others)",     "num",  True),
    ("total_consume_qty",   "Total Consume Qty",   "num",  True),
    ("cls_qty",             "ClsQty",              "num",  True),
    ("cls_qty_slr",         "ClsQty(SLR)",         "num",  True),
    ("remark",              "Remark",              "text", True),
]

OK = "OK"
EXCEPTION = "Exception"

# Quantities carry at most a few decimals; this removes float noise such as 1e-13 from sums
QTY_DECIMALS = 6

_HEADER_RE = re.compile(r"[^a-z0-9]")


def _norm_header(h) -> str:
    return _HEADER_RE.sub("", str(h).lower())


def _find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lookup = {}
    for c in df.columns:
        lookup.setdefault(_norm_header(c), c)
    for alias in aliases:
        if alias in lookup:
            return lookup[alias]
    return None


def _is_blank(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    # "nan" is what the HTML-table fallback of the loader leaves in empty cells
    return str(val).strip().lower() in ("", "nan")


def _code_text(val) -> str:
    """Item code as shown in the file; whole numbers lose the '.0' a numeric cell can pick up."""
    if _is_blank(val):
        return ""
    s = str(val)
    if s.endswith(".0") and s[:-2].strip().lstrip("-").isdigit():
        s = s[:-2]
    return s


def _sumif_key(code: str) -> str:
    """SUMIF criteria match: case-insensitive, no trimming."""
    return code.upper()


def _to_float(val) -> float:
    """SUMIF ignores blank and text cells in the sum range, so they count as 0."""
    if _is_blank(val):
        return 0.0
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return 0.0


def _clean(num: float) -> float:
    r = round(num, QTY_DECIMALS)
    return 0.0 if r == 0 else r


def _excel_round(num: float, digits: int) -> Decimal:
    """Excel ROUND: half away from zero on the 15-significant-digit value Excel works with."""
    return Decimal(f"{num:.15g}").quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)


def _parse_dates(series: pd.Series) -> pd.Series:
    """ERP exports arrive as ISO ('2026-02-06 00:00:00') or day-first ('06-02-2026') text."""
    iso = pd.to_datetime(series, errors="coerce", format="ISO8601")
    return iso.fillna(pd.to_datetime(series.where(iso.isna()), errors="coerce", dayfirst=True, format="mixed"))


def _format_date(ts) -> str | None:
    if ts is None or pd.isna(ts):
        return None
    return ts.strftime("%Y-%m-%d")


def _column_meta() -> list[dict]:
    return [{"id": cid, "label": label, "type": kind, "computed": computed} for cid, label, kind, computed in COLUMNS]


def _empty_result(error: str) -> dict:
    return {"columns": _column_meta(), "rows": [], "kpis": {}, "error": error}


def run_stock_verified_report(dfs: dict[str, pd.DataFrame]) -> dict:
    df_inv = dfs.get("inventory_report")
    if df_inv is None or df_inv.empty:
        return _empty_result("Inventory Report not uploaded.")

    inv_cols = {fid: _find_col(df_inv, aliases) for fid, _, aliases in INVENTORY_FIELDS}
    missing = [INVENTORY_LABEL[f] for f in ["item_code"] + INVENTORY_QTY_FIELDS if not inv_cols[f]]
    if missing:
        return _empty_result(f"Inventory Report is missing required column(s): {', '.join(missing)}.")

    warnings = []

    # ── Purchase Register: Quantity per item code (column H) ─────────────────────
    pr_qty: dict[str, float] = {}
    pr_codes_display: dict[str, str] = {}
    pr_lines = 0
    df_pr = dfs.get("purchase_register")
    if df_pr is None or df_pr.empty:
        warnings.append("Purchase Register not uploaded — RecQty PR(GRPO) is 0 for every item.")
    else:
        pr_cols = {fid: _find_col(df_pr, aliases) for fid, _, aliases in PR_FIELDS}
        pr_missing = [PR_LABEL[f] for f in pr_cols if not pr_cols[f]]
        if pr_missing:
            warnings.append(
                f"Purchase Register is missing column(s): {', '.join(pr_missing)} — RecQty PR(GRPO) is 0 for every item."
            )
        else:
            for code_raw, qty_raw in zip(df_pr[pr_cols["item_code"]], df_pr[pr_cols["quantity"]]):
                code = _code_text(code_raw)
                if not code:
                    continue
                key = _sumif_key(code)
                pr_qty[key] = pr_qty.get(key, 0.0) + _to_float(qty_raw)
                pr_codes_display.setdefault(key, code)
                pr_lines += 1

    # ── Inventory Report: one entry per item code, warehouse lines summed ──────
    n = len(df_inv)
    blank_col = [None] * n

    def column(fid):
        return df_inv[inv_cols[fid]].tolist() if inv_cols[fid] else blank_col

    def date_column(fid):
        return _parse_dates(df_inv[inv_cols[fid]]).tolist() if inv_cols[fid] else blank_col

    def text_of(val):
        return None if _is_blank(val) else str(val).strip()

    codes = column("item_code")
    from_dates, to_dates = date_column("from_date"), date_column("to_date")
    names, uoms, groups = column("item_name"), column("uom"), column("item_group")
    qty_cols = {f: [_to_float(v) for v in column(f)] for f in INVENTORY_QTY_FIELDS}

    items: dict[str, dict] = {}
    inventory_lines = 0
    blank_code_lines = 0
    for i in range(n):
        code = _code_text(codes[i])
        if not code:
            blank_code_lines += 1
            continue
        inventory_lines += 1
        key = _sumif_key(code)
        item = items.get(key)
        if item is None:
            item = {
                "from_date":  _format_date(from_dates[i]),
                "to_date":    _format_date(to_dates[i]),
                "item_code":  code,
                "item_name":  text_of(names[i]),
                "uom":        text_of(uoms[i]),
                "item_group": text_of(groups[i]),
                "_lines":     0,
                **{f: 0.0 for f in INVENTORY_QTY_FIELDS},
            }
            items[key] = item
        item["_lines"] += 1
        for f in INVENTORY_QTY_FIELDS:
            item[f] += qty_cols[f][i]

    if blank_code_lines:
        warnings.append(f"{blank_code_lines:,} Inventory Report line(s) have no Item_Code and are not included.")

    # ── Calculated columns ──────────────────────────────────────────────────────
    rows = []
    for key, it in items.items():
        ob = it["ob_qty"]
        pr = pr_qty.get(key, 0.0)
        stock = it["rec_qty_grpo"]
        rec_others = it["rec_qty_others"]
        out_cons = it["out_qty_consumption"]
        out_others = it["out_qty_others"]
        cls_slr = it["cls_qty"]

        variation = _clean(stock - pr)
        total_rec = ob + stock + rec_others
        total_consume = out_cons + out_others
        cls_calc = total_rec - total_consume

        rows.append({
            "from_date":           it["from_date"],
            "to_date":             it["to_date"],
            "item_code":           it["item_code"],
            "item_name":           it["item_name"],
            "uom":                 it["uom"],
            "item_group":          it["item_group"],
            "ob_qty":              _clean(ob),
            "pr_rec_qty":          _clean(pr),
            "stock_rec_qty":       _clean(stock),
            "variation":           variation,
            "remark_pr":           EXCEPTION if variation < 0 else OK,
            "rec_qty_others":      _clean(rec_others),
            "total_rec_qty":       _clean(total_rec),
            "out_qty_consumption": _clean(out_cons),
            "out_qty_others":      _clean(out_others),
            "total_consume_qty":   _clean(total_consume),
            "cls_qty":             _clean(cls_calc),
            "cls_qty_slr":         _clean(cls_slr),
            # compared after float noise is removed: Excel's own sheet flags 2320.6149999999907 vs 2320.615
            "remark":              OK if _excel_round(_clean(cls_calc), 2) == _excel_round(_clean(cls_slr), 2) else EXCEPTION,
            "warehouse_lines":     it["_lines"],
        })

    # Purchase Register items with no Inventory Report line never reach the report — list them
    pr_not_in_inventory = [
        {"item_code": pr_codes_display[k], "pr_rec_qty": _clean(q)}
        for k, q in pr_qty.items() if k not in items
    ]
    if pr_not_in_inventory:
        warnings.append(
            f"{len(pr_not_in_inventory):,} Purchase Register item code(s) are not in the Inventory Report, "
            "so their purchased quantity is not checked."
        )

    kpis = {
        "total_items":         len(rows),
        "inventory_lines":     inventory_lines,
        "pr_lines":            pr_lines,
        "pr_exceptions":       sum(1 for r in rows if r["remark_pr"] == EXCEPTION),
        "closing_exceptions":  sum(1 for r in rows if r["remark"] == EXCEPTION),
        "pr_not_in_inventory": len(pr_not_in_inventory),
    }

    return {
        "columns": _column_meta(),
        "rows": rows,
        "kpis": kpis,
        "pr_not_in_inventory": pr_not_in_inventory,
        "warnings": warnings,
    }
