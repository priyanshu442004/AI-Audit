"""
Module — GRN to AP Invoice Check (Phase 1–3).

Columns populated per GRPO Report row (no joins):
  GRN No.       ← GRPO No.       (canonical: grpo_no)
  GRN Date      ← Document Date  (canonical: posting_date)
  PO Number     ← PO Number      (canonical: po_no)
  Vendor Code   ← Vendor Code    (canonical: vendor_code)
  Vendor Name   ← Vendor Name    (canonical: vendor_name)

Columns populated via GRPO-Number join to AP Invoice Report (or Purchase Register):
  AP Invoice No.  ← AP Invoice No.   (canonical: invoice_no)
  Invoice Date    ← Document Date    (canonical: posting_date, fallback: invoice_date)

Join key: GRPO's GRPO No. ↔ AP Invoice Report's GRPO Number column.
One output row per GRPO Report row; first matching AP Invoice record wins per GRPO No.
Remaining columns are set to None until subsequent phases add them.
"""

from __future__ import annotations

import pandas as pd

from app.cleaning import detect_columns
from app.analysis.calculated_fields import field, same_row


_TABLE_COLUMNS = [
    "GRN No.",
    "GRN Date",
    "AP Invoice No.",
    "Invoice Date",
    "PO Number",
    "Vendor Code",
    "Vendor Name",
    "Vendor Country",
    "PO Qty",
    "PO Price",
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


def _safe_num(val) -> float | None:
    """Return a float from a raw cell value, stripping thousand-separator commas. None for blank/invalid."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return None if (isinstance(val, float) and pd.isna(val)) else float(val)
    s = str(val).strip().replace(",", "")
    if not s or s.lower() in ("nan", "none", "nat", ""):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _safe_int(val) -> int | None:
    """Return an integer from a raw cell value (truncates decimals). None for blank/invalid."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    try:
        return int(float(str(val).strip().replace(",", "")))
    except (ValueError, TypeError):
        return None


def _seq_exception(raw_grn, raw_inv) -> int | None:
    """Return 1 if invoice date precedes GRN date, 0 if on or after, None if either is missing/invalid."""
    if raw_grn is None or raw_inv is None:
        return None
    try:
        d_grn = pd.to_datetime(raw_grn, errors="coerce", dayfirst=True)
        d_inv = pd.to_datetime(raw_inv, errors="coerce", dayfirst=True)
        if pd.isna(d_grn) or pd.isna(d_inv):
            return None
        return 1 if d_inv < d_grn else 0
    except Exception:
        return None


def _calc_days(raw_from, raw_to) -> int | None:
    """Return absolute integer calendar days between two raw date values.
    Both inputs are raw cell values; returns None if either is missing or invalid."""
    if raw_from is None or raw_to is None:
        return None
    try:
        d_from = pd.to_datetime(raw_from, errors="coerce", dayfirst=True)
        d_to   = pd.to_datetime(raw_to,   errors="coerce", dayfirst=True)
        if pd.isna(d_from) or pd.isna(d_to):
            return None
        return abs(int((d_to - d_from).days))
    except Exception:
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
    col_po_qty    = grpo_map.get("po_qty")
    col_po_price  = next(
        (c for c in df_grpo.columns if c.strip().lower() == "po price"),
        None,
    )
    col_doc_currency = next(
        (c for c in df_grpo.columns if c.strip().lower() == "document currency"),
        None,
    )

    # ── Build AP Invoice lookup: GRPO Number → first matching invoice record ──
    # Prefer the dedicated AP Invoice Report; fall back to Purchase Register.
    # Join key: GRPO's GRPO No. ↔ AP Invoice Report's GRPO Number column.
    # "AP Invoice No." → invoice_no canonical
    # "Document Date"  → posting_date canonical (fallback: invoice_date)
    #
    # inv_lookup: { normalized_grpo_no: {"invoice_no": str|None, "invoice_date": str|None} }
    inv_lookup: dict[str, dict] = {}
    df_ap = dfs.get("ap_invoice_report")
    if df_ap is None:
        df_ap = dfs.get("purchase_register")
    if df_ap is not None and not df_ap.empty:
        ap_map        = detect_columns(df_ap)
        col_ap_grpo   = ap_map.get("grpo_no")
        col_ap_inv    = ap_map.get("invoice_no")
        col_ap_lt     = ap_map.get("line_total")
        # Invoice Date must come from "Document Date" when that column exists.
        # posting_date alias list checks "posting date" before "document date",
        # so we check the exact header first to avoid picking the wrong column.
        _ap_doc_date = next(
            (c for c in df_ap.columns if c.strip().lower() == "document date"),
            None,
        )
        col_ap_date  = _ap_doc_date or ap_map.get("posting_date") or ap_map.get("invoice_date")

        if col_ap_grpo and col_ap_inv:
            for _, ap_row in df_ap.iterrows():
                grpo_key = _normalize_id(ap_row[col_ap_grpo])
                if grpo_key and grpo_key not in inv_lookup:  # first invoice per GRPO No. wins
                    inv_lookup[grpo_key] = {
                        "invoice_no":       _safe_str(ap_row[col_ap_inv]),
                        "invoice_date":     _fmt_date(ap_row[col_ap_date]) if col_ap_date else None,
                        "invoice_date_raw": ap_row[col_ap_date] if col_ap_date else None,
                        "invoice_value":    _safe_num(ap_row[col_ap_lt]) if col_ap_lt else None,
                    }

    # ── Build one output row per GRPO Report row ──────────────────────────────
    rows = []
    for _, grpo_row in df_grpo.iterrows():
        grpo_key        = _normalize_id(grpo_row[col_grn]) if col_grn else ""
        inv_info        = inv_lookup.get(grpo_key, {})
        grn_date_raw    = grpo_row[col_grn_date] if col_grn_date else None
        inv_date_raw    = inv_info.get("invoice_date_raw")
        days_grn_inv    = _calc_days(grn_date_raw, inv_date_raw)
        seq_exception   = _seq_exception(grn_date_raw, inv_date_raw)

        rows.append({
            "GRN No.":                    _safe_str(grpo_row[col_grn])           if col_grn      else None,
            "GRN Date":                   _fmt_date(grpo_row[col_grn_date])      if col_grn_date else None,
            "AP Invoice No.":             inv_info.get("invoice_no"),
            "Invoice Date":               inv_info.get("invoice_date"),
            "PO Number":                  _safe_str(grpo_row[col_po])       if col_po       else None,
            "Vendor Code":                _safe_str(grpo_row[col_ven_code]) if col_ven_code else None,
            "Vendor Name":                _safe_str(grpo_row[col_ven_name]) if col_ven_name else None,
            "Vendor Country":             "India" if col_doc_currency and str(grpo_row[col_doc_currency]).strip().upper() == "INR" else ("USA" if col_doc_currency else None),
            "PO Qty":                     _safe_int(grpo_row[col_po_qty])   if col_po_qty   else None,
            "PO Price":                   _safe_num(grpo_row[col_po_price]) if col_po_price else None,
            "Invoice Value (INR)":        inv_info.get("invoice_value"),
            "Days GRN→Inv":               days_grn_inv,
            "Within 7-day SLA":           (1 if days_grn_inv <= 7 else 0) if days_grn_inv is not None else None,
            "Invoice > 7 days (Breach)":  (1 if days_grn_inv >  7 else 0) if days_grn_inv is not None else None,
            "Seq Exception (Inv<GRN)":    seq_exception,
        })

    # ── KPI computations from reconciliation rows ─────────────────────────────
    days_vals   = [r["Days GRN→Inv"]            for r in rows if r["Days GRN→Inv"]            is not None]
    sla_vals    = [r["Within 7-day SLA"]         for r in rows if r["Within 7-day SLA"]         is not None]
    breach_vals = [r["Invoice > 7 days (Breach)"] for r in rows if r["Invoice > 7 days (Breach)"] is not None]
    seq_vals    = [r["Seq Exception (Inv<GRN)"]  for r in rows if r["Seq Exception (Inv<GRN)"]  is not None]

    within_sla  = sum(sla_vals)
    breach      = sum(breach_vals)
    denominator = within_sla + breach
    sla_pct     = f"{within_sla / denominator * 100:.1f}%" if denominator else "—"

    flagged = [
        r for r in rows
        if r.get("Invoice > 7 days (Breach)") == 1 or r.get("Seq Exception (Inv<GRN)") == 1
    ]

    kpis = {
        "invoices_linked_to_grn": len({r["AP Invoice No."] for r in rows if r.get("AP Invoice No.") not in (None, "")}),
        "within_7_day_sla":       within_sla,
        "breach_gt_7_days":       breach,
        "sla_compliance_pct":     sla_pct,
        "avg_days_grn_to_inv":    round(sum(days_vals) / len(days_vals), 2) if days_vals else None,
        "max_days_grn_to_inv":    max(days_vals) if days_vals else None,
        "sequence_exceptions":    sum(seq_vals),
        "unique_po_numbers":      len({r["PO Number"]      for r in rows if r.get("PO Number")      not in (None, "")}),
        "unique_grn_nos":         len({r["GRN No."]        for r in rows if r.get("GRN No.")        not in (None, "")}),
        "unique_ap_invoices":     len({r["AP Invoice No."] for r in rows if r.get("AP Invoice No.") not in (None, "")}),
        "unique_pos_flagged":     len({r["PO Number"] for r in flagged if r.get("PO Number") not in (None, "")}),
        "unique_grns_flagged":    len({r["GRN No."]   for r in flagged if r.get("GRN No.")   not in (None, "")}),
    }

    return {
        "kpis":   kpis,
        "charts": {},
        "tables": [
            {
                "title": "GRN to AP Invoice Full Reconciliation List",
                "rows": rows,
                "calculated_fields": {
                    "Days GRN→Inv": field(
                        "Invoice Date − GRN Date",
                        "ABS(Invoice_Date − GRN_Date)",
                        inputs=[
                            {"field": "GRN Date", "source_file": "GRPO Report", "source_record": "GRN No."},
                            {"field": "Invoice Date", "source_file": "AP Invoice Report", "source_record": "AP Invoice No."},
                        ],
                    ),
                    "Within 7-day SLA": field(
                        "Days GRN→Inv ≤ 7 days",
                        "IF(Days_GRN_Inv ≤ 7, 1, 0)",
                        inputs=[{"field": "Days GRN→Inv", "source_file": "GRPO Report (calculated)", "source_record": "GRN No."}],
                    ),
                    "Invoice > 7 days (Breach)": field(
                        "Days GRN→Inv > 7 days",
                        "IF(Days_GRN_Inv > 7, 1, 0)",
                        inputs=[{"field": "Days GRN→Inv", "source_file": "GRPO Report (calculated)", "source_record": "GRN No."}],
                    ),
                    "Seq Exception (Inv<GRN)": field(
                        "Invoice Date < GRN Date",
                        "IF(Invoice_Date < GRN_Date, 1, 0)",
                        inputs=[
                            {"field": "GRN Date", "source_file": "GRPO Report", "source_record": "GRN No."},
                            {"field": "Invoice Date", "source_file": "AP Invoice Report", "source_record": "AP Invoice No."},
                        ],
                    ),
                },
            },
        ],
    }