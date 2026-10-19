"""
Vendor Price Comparison Analysis — built from the Purchase Order Report.

Two modules, each reproducing the auditor's Excel workings:

Same Vendor  — one line per distinct (Item Code, PO Price) so every price an item
               was bought at can be compared, vendor by vendor.
    1. Document Currency = INR
    2. Vendor Group is not Group Company / Foreign
    3. Document Status = Closed
    4. Item Code appears on more than one line of the whole PO report
    5. Sort by Item Code (numeric codes first, like Excel), then Posting Date
    6. Remove duplicate Price Key (Item Code-PO Price), keeping the first line
    Helper columns (computed on the resulting sheet, as the Excel COUNTIFs do):
      Duplicate Vendor Code = YES if the Vendor Code appears more than once
      Duplicate Item Code   = YES if the Item Code appears more than once
      Price Key             = Item Code & "-" & PO Price

Different Vendor — one line per vendor per item, for items bought from 2+ vendors.
    1. Document Currency = INR
    2. Vendor Group is not Group Company / Foreign
    3. Item Code is bought from at least two distinct Vendor Codes in the PO report
    4. Sort by Item Code, then Posting Date
    5. Remove duplicate Key (Vendor Code-Item Code), keeping the first line
    6. Remove duplicate Price Key (Item Code-PO Price), keeping the first line
    Helper columns:
      Duplicate Item Code = YES if the Item Code appears more than once
      Key                 = Vendor Code & "-" & Item Code
      Price Key           = Item Code & "-" & PO Price

Canceled PO lines (Canceled Status = Yes) are excluded from both modules.
"""

from __future__ import annotations

import math
import re

import pandas as pd


# (id, label, aliases, kind) — kind: "id" | "text" | "date" | "num"
SOURCE_FIELDS = [
    ("numerator",         "Numerator",         ["numerator", "doc entry", "docentry"], "id"),
    ("po_no",             "PO No",             ["po no", "po no.", "po number", "purchase order no", "purchase order number"], "id"),
    ("po_series",         "PO Series",         ["po series", "series"], "text"),
    ("posting_date",      "Posting Date",      ["posting date", "post date", "postingdate", "po date"], "date"),
    ("delivery_date",     "Delivery Date",     ["delivery date", "deliverydate"], "date"),
    ("document_date",     "Document Date",     ["document date", "doc date", "documentdate"], "date"),
    ("branch",            "Branch",            ["branch", "branch name"], "text"),
    ("document_status",   "Document Status",   ["document status", "doc status", "status"], "text"),
    ("canceled_status",   "Canceled Status",   ["canceled status", "cancelled status", "canceled", "cancelled"], "text"),
    ("vendor_group",      "Vendor Group",      ["vendor group", "vendor_group"], "text"),
    ("vendor_code",       "Vendor Code",       ["vendor code", "vendor_code", "card code", "cardcode"], "id"),
    ("vendor_name",       "Vendor Name",       ["vendor name", "vendor_name", "card name", "cardname"], "text"),
    ("item_group",        "Item Group",        ["item group", "item_group"], "text"),
    ("item_code",         "Item Code",         ["item code", "item_code", "item no", "item no.", "itemno"], "id"),
    ("item_description",  "Item Description",  ["item description", "item_description", "description", "itemname"], "text"),
    ("uom",               "UOM",               ["uom", "unit"], "text"),
    ("po_qty",            "PO Qty",            ["po qty", "po_qty", "ordered qty", "quantity", "qty"], "num"),
    ("po_price",          "PO Price",          ["po price", "po_price", "unit price", "price"], "num"),
    ("document_currency", "Document Currency", ["document currency", "doc currency", "currency"], "text"),
    ("document_rate",     "Document Rate",     ["document rate", "doc rate", "documentrate"], "num"),
    ("line_total",        "Line Total",        ["line total", "line_total"], "num"),
    ("document_total",    "Document Total",    ["document total", "doc total", "document_total"], "num"),
    ("warehouse_code",    "Warehouse Code",    ["warehouse code", "warehouse", "whs code"], "text"),
    ("open_qty",          "Open Qty",          ["open qty", "open_qty", "open quantity"], "num"),
]

SOURCE_KIND = {f[0]: f[3] for f in SOURCE_FIELDS}
SOURCE_LABEL = {f[0]: f[1] for f in SOURCE_FIELDS}

COMPUTED_FIELDS = {
    "duplicate_vendor_code": "Duplicate Vendor Code",
    "duplicate_item_code":   "Duplicate Item Code",
    "price_key":             "Price Key",
    "key":                   "Key",
}

# Column layout of each module, exactly as in the Excel workings
SAME_VENDOR_COLUMNS = [
    "numerator", "po_no", "po_series", "posting_date", "delivery_date", "document_date",
    "branch", "document_status", "canceled_status", "vendor_group", "vendor_code",
    "duplicate_vendor_code", "vendor_name", "item_group", "item_code", "duplicate_item_code",
    "item_description", "uom", "po_qty", "po_price", "price_key", "document_currency",
    "document_rate", "line_total", "document_total", "warehouse_code", "open_qty",
]

DIFFERENT_VENDOR_COLUMNS = [
    "numerator", "po_no", "po_series", "posting_date", "delivery_date", "document_date",
    "branch", "document_status", "canceled_status", "vendor_group", "vendor_code",
    "vendor_name", "item_group", "item_code", "duplicate_item_code", "key",
    "item_description", "uom", "po_qty", "po_price", "price_key", "document_currency",
    "document_rate", "line_total", "document_total", "warehouse_code", "open_qty",
]

BASE_CURRENCY = "INR"
EXCLUDED_VENDOR_GROUP_TERMS = ("group company", "foreign")
CLOSED_STATUS = "closed"
CANCELED_VALUES = {"yes", "y", "canceled", "cancelled"}

_NUMERIC_ID_RE = re.compile(r"^\d+$")


def _find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    lookup = {str(c).lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias in lookup:
            return lookup[alias]
    return None


def _is_blank(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    return str(val).strip().lower() in ("", "nan", "none", "nat")


def _normalize_id(val) -> str:
    if _is_blank(val):
        return ""
    s = str(val).strip()
    if s.endswith(".0") and s[:-2].lstrip("-").isdigit():
        s = s[:-2]
    return s


def _to_float(val) -> float | None:
    if _is_blank(val):
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return None


def _excel_number_text(num: float) -> str:
    """Text Excel produces when a number is concatenated (CONCAT / &): up to 15 significant digits."""
    if float(num).is_integer() and abs(num) < 1e15:
        return str(int(num))
    return f"{num:.15g}".upper()


def _parse_dates(series: pd.Series) -> pd.Series:
    """ERP exports arrive as ISO ('2026-02-06 00:00:00') or day-first ('06-02-2026') text."""
    iso = pd.to_datetime(series, errors="coerce", format="ISO8601")
    return iso.fillna(pd.to_datetime(series.where(iso.isna()), errors="coerce", dayfirst=True, format="mixed"))


def _format_date(ts) -> str | None:
    if ts is None or pd.isna(ts):
        return None
    return ts.strftime("%Y-%m-%d")


def _empty_module(columns: list[str]) -> dict:
    return {"columns": _column_meta(columns), "rows": []}


def _column_meta(columns: list[str]) -> list[dict]:
    meta = []
    for cid in columns:
        if cid in COMPUTED_FIELDS:
            meta.append({"id": cid, "label": COMPUTED_FIELDS[cid], "type": "text", "computed": True})
        else:
            meta.append({"id": cid, "label": SOURCE_LABEL[cid], "type": SOURCE_KIND[cid], "computed": False})
    return meta


def _excel_sort(df: pd.DataFrame) -> pd.DataFrame:
    """Excel ascending sort on Item Code (numbers before text), then Posting Date, then file order."""
    return df.sort_values(["_ic_is_text", "_ic_num", "_ic_text", "_post", "_order"], kind="stable", na_position="last")


def _build_rows(df: pd.DataFrame, cols: dict[str, str | None], columns: list[str], computed: dict[str, pd.Series]) -> list[dict]:
    rows = []
    for idx, rec in df.iterrows():
        row = {}
        for cid in columns:
            if cid in computed:
                row[cid] = computed[cid].loc[idx]
                continue
            src = cols.get(cid)
            raw = rec[src] if src else None
            kind = SOURCE_KIND[cid]
            if kind == "num":
                row[cid] = _to_float(raw)
            elif kind == "date":
                row[cid] = _format_date(rec[f"_date_{cid}"])
            elif kind == "id":
                row[cid] = _normalize_id(raw) or None
            else:
                row[cid] = None if _is_blank(raw) else str(raw).strip()
        rows.append(row)
    return rows


def _yes_no_duplicates(series: pd.Series) -> pd.Series:
    counts = series.map(series.value_counts())
    return counts.gt(1).map({True: "YES", False: "NO"})


def run_vendor_price_comparison(dfs: dict[str, pd.DataFrame]) -> dict:
    df_po = dfs.get("purchase_order")
    if df_po is None or df_po.empty:
        return {
            "same_vendor": _empty_module(SAME_VENDOR_COLUMNS),
            "different_vendor": _empty_module(DIFFERENT_VENDOR_COLUMNS),
            "error": "Purchase Order Report not uploaded.",
        }

    cols = {fid: _find_col(df_po, aliases) for fid, _, aliases, _ in SOURCE_FIELDS}
    missing = [SOURCE_LABEL[f] for f in ("item_code", "vendor_code", "po_price") if not cols[f]]
    if missing:
        return {
            "same_vendor": _empty_module(SAME_VENDOR_COLUMNS),
            "different_vendor": _empty_module(DIFFERENT_VENDOR_COLUMNS),
            "error": f"Purchase Order Report is missing required column(s): {', '.join(missing)}.",
        }

    w = df_po.copy()
    w["_order"] = range(len(w))

    item_disp = w[cols["item_code"]].map(_normalize_id)
    vendor_disp = w[cols["vendor_code"]].map(_normalize_id)
    w["_item"] = item_disp
    w["_vendor"] = vendor_disp
    # Excel text comparisons (COUNTIF / Remove Duplicates) are case-insensitive
    w["_ic"] = item_disp.str.upper()
    w["_vc"] = vendor_disp.str.upper()

    w["_price"] = w[cols["po_price"]].map(_to_float)
    w["_price_txt"] = w["_price"].map(lambda p: _excel_number_text(p) if p is not None and not pd.isna(p) else "")

    w["_ic_is_text"] = (~item_disp.str.fullmatch(_NUMERIC_ID_RE)).astype(int)
    w["_ic_num"] = pd.to_numeric(item_disp.where(w["_ic_is_text"] == 0), errors="coerce").fillna(0)
    w["_ic_text"] = item_disp.str.lower()
    for fid, _, _, kind in SOURCE_FIELDS:
        if kind == "date":
            w[f"_date_{fid}"] = _parse_dates(w[cols[fid]]) if cols[fid] else pd.NaT
    w["_post"] = w["_date_posting_date"]

    w = w[(w["_ic"] != "") & (w["_vc"] != "")]

    # Counts over the whole PO report, as the auditor's item checks are done on the full file
    item_line_count = w.groupby("_ic").size()
    item_vendor_count = w.groupby("_ic")["_vc"].nunique()

    base = w["_price_txt"] != ""
    if cols["document_currency"]:
        base &= w[cols["document_currency"]].fillna("").astype(str).str.strip().str.upper() == BASE_CURRENCY
    if cols["vendor_group"]:
        vg = w[cols["vendor_group"]].fillna("").astype(str).str.strip().str.lower()
        for term in EXCLUDED_VENDOR_GROUP_TERMS:
            base &= ~vg.str.contains(term, regex=False)
    if cols["canceled_status"]:
        base &= ~w[cols["canceled_status"]].fillna("").astype(str).str.strip().str.lower().isin(CANCELED_VALUES)

    # ── Same Vendor ────────────────────────────────────────────────────────────
    sv_mask = base & (w["_ic"].map(item_line_count) > 1)
    if cols["document_status"]:
        sv_mask &= w[cols["document_status"]].fillna("").astype(str).str.strip().str.lower() == CLOSED_STATUS
    sv = _excel_sort(w[sv_mask]).drop_duplicates(["_ic", "_price_txt"], keep="first")
    sv_computed = {
        "duplicate_vendor_code": _yes_no_duplicates(sv["_vc"]),
        "duplicate_item_code":   _yes_no_duplicates(sv["_ic"]),
        "price_key":             sv["_item"] + "-" + sv["_price_txt"],
    }

    # ── Different Vendor ───────────────────────────────────────────────────────
    dv_mask = base & (w["_ic"].map(item_vendor_count) > 1)
    dv = (
        _excel_sort(w[dv_mask])
        .drop_duplicates(["_vc", "_ic"], keep="first")
        .drop_duplicates(["_ic", "_price_txt"], keep="first")
    )
    dv_computed = {
        "duplicate_item_code": _yes_no_duplicates(dv["_ic"]),
        "key":                 dv["_vendor"] + "-" + dv["_item"],
        "price_key":           dv["_item"] + "-" + dv["_price_txt"],
    }

    return {
        "same_vendor": {
            "columns": _column_meta(SAME_VENDOR_COLUMNS),
            "rows": _build_rows(sv, cols, SAME_VENDOR_COLUMNS, sv_computed),
        },
        "different_vendor": {
            "columns": _column_meta(DIFFERENT_VENDOR_COLUMNS),
            "rows": _build_rows(dv, cols, DIFFERENT_VENDOR_COLUMNS, dv_computed),
        },
    }
