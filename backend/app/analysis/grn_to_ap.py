"""
Module — GRN to AP Invoice Check (Phase 1–3).

Columns populated per GRPO Report row (no joins):
  GRN No.       ← GRPO No.       (canonical: grpo_no)
  GRN Date      ← Document Date  (canonical: posting_date)
  PO Number     ← PO Number      (canonical: po_no)
  Vendor Code   ← Vendor Code    (canonical: vendor_code)
  Vendor Name   ← Vendor Name    (canonical: vendor_name)

Columns populated via PO-Number join to AP Invoice Report (or Purchase Register):
  AP Invoice No.  ← AP Invoice No.   (canonical: invoice_no)
  Invoice Date    ← Document Date    (canonical: posting_date, fallback: invoice_date)

Join key: GRPO's PO Number ↔ AP Invoice Report's PO Number.
One output row per GRPO Report row; first matching AP Invoice record wins per PO.
Remaining columns are set to None until subsequent phases add them.
"""

from __future__ import annotations

import pandas as pd

from app.cleaning import detect_columns


_TABLE_COLUMNS = [
    "GRN No.",
    "GRN Date",
    "AP Invoice No.",
    "Invoice Date",
    "AP Credit Note No.",
    "PO Number",
    "Vendor Code",
    "Vendor Name",
    "Vendor Country",
    "Items",
    "Invoice Value (INR)",
    "Days GRN→Inv",
    "Within 7-day SLA",
    "Invoice > 7 days (Breach)",
    "Seq Exception (Inv<GRN)",
]

_EMPTY_RESULT = {
    "kpis":   {},
    "charts": {},
    "tables": [
        {"title": "GRN to AP Invoice Full Reconciliation List", "rows": []},
    ],
}


def _safe_str(val) -> str | None:
    """Return a stripped string value, or None for blank / NaN / null inputs."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    if s.lower() in ("nan", "none", "nat", ""):
        return None
    return s


def _normalize_id(val) -> str:
    """Uppercase and strip trailing .0 for consistent ID comparison."""
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    s = str(val).strip().upper()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def _fmt_date(val) -> str | None:
    """Parse any date value and return DD/MM/YY string, or None if unparseable."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    try:
        dt = pd.to_datetime(val, errors="coerce", dayfirst=True)
        if pd.notna(dt):
            return dt.strftime("%d/%m/%y")
    except Exception:
        pass
    return None


def run(dfs: dict) -> dict:
    df_grpo = dfs.get("grpo")

    if df_grpo is None or df_grpo.empty:
        return _EMPTY_RESULT

    # ── Detect source columns from the GRPO Report ───────────────────────────
    # grpo_no:      "GRPO No", "GRPO No.", "Receipt No", "Goods Receipt No", …
    # posting_date: "Document Date", "Posting Date", "Doc Date", "Date", …
    # po_no:        "PO Number", "PO No", "Purchase Order No", …
    # vendor_code:  "Vendor Code", "BP Code", "Supplier Code", …
    # vendor_name:  "Vendor Name", "BP Name", "Supplier Name", …
    grpo_map      = detect_columns(df_grpo)
    col_grn       = grpo_map.get("grpo_no")
    col_grn_date  = grpo_map.get("posting_date") or grpo_map.get("grpo_date")
    col_po        = grpo_map.get("po_no")
    col_ven_code  = grpo_map.get("vendor_code")
    col_ven_name  = grpo_map.get("vendor_name")

    # ── Build AP Invoice lookup: PO Number → first matching invoice record ────
    # Prefer the dedicated AP Invoice Report; fall back to Purchase Register.
    # Join key: GRPO's PO Number ↔ AP Invoice Report's PO Number.
    # "AP Invoice No." → invoice_no canonical
    # "Document Date"  → posting_date canonical (fallback: invoice_date)
    #
    # inv_lookup: { normalized_po_no: {"invoice_no": str|None, "invoice_date": str|None} }
    inv_lookup: dict[str, dict] = {}
    df_ap = dfs.get("ap_invoice_report")
    if df_ap is None:
        df_ap = dfs.get("purchase_register")
    if df_ap is not None and not df_ap.empty:
        ap_map       = detect_columns(df_ap)
        col_ap_po    = ap_map.get("po_no") or ap_map.get("pr_po_no")
        col_ap_inv   = ap_map.get("invoice_no")
        # Invoice Date must come from "Document Date" when that column exists.
        # posting_date alias list checks "posting date" before "document date",
        # so we check the exact header first to avoid picking the wrong column.
        _ap_doc_date = next(
            (c for c in df_ap.columns if c.strip().lower() == "document date"),
            None,
        )
        col_ap_date  = _ap_doc_date or ap_map.get("posting_date") or ap_map.get("invoice_date")

        if col_ap_po and col_ap_inv:
            for _, ap_row in df_ap.iterrows():
                po_key = _normalize_id(ap_row[col_ap_po])
                if po_key and po_key not in inv_lookup:  # first invoice per PO wins
                    inv_lookup[po_key] = {
                        "invoice_no":   _safe_str(ap_row[col_ap_inv]),
                        "invoice_date": _fmt_date(ap_row[col_ap_date]) if col_ap_date else None,
                    }

    # ── Build one output row per GRPO Report row ──────────────────────────────
    rows = []
    for _, grpo_row in df_grpo.iterrows():
        po_key   = _normalize_id(grpo_row[col_po]) if col_po else ""
        inv_info = inv_lookup.get(po_key, {})

        rows.append({
            "GRN No.":                    _safe_str(grpo_row[col_grn])           if col_grn      else None,
            "GRN Date":                   _fmt_date(grpo_row[col_grn_date])      if col_grn_date else None,
            "AP Invoice No.":             inv_info.get("invoice_no"),
            "Invoice Date":               inv_info.get("invoice_date"),
            "AP Credit Note No.":         None,
            "PO Number":                  _safe_str(grpo_row[col_po])       if col_po       else None,
            "Vendor Code":                _safe_str(grpo_row[col_ven_code]) if col_ven_code else None,
            "Vendor Name":                _safe_str(grpo_row[col_ven_name]) if col_ven_name else None,
            "Vendor Country":             None,
            "Items":                      None,
            "Invoice Value (INR)":        None,
            "Days GRN→Inv":               None,
            "Within 7-day SLA":           None,
            "Invoice > 7 days (Breach)":  None,
            "Seq Exception (Inv<GRN)":    None,
        })

    return {
        "kpis":   {},
        "charts": {},
        "tables": [
            {"title": "GRN to AP Invoice Full Reconciliation List", "rows": rows},
        ],
    }
