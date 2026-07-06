"""
Module — GE to GRN Check (Phase 1: GRPO data mapping).

Reads the GRPO Report and populates five columns of the reconciliation table:
  GRN No.         ← GRPO No
  Gate Entry No.  ← Gate Entry No
  PO Number       ← PO Number
  Vendor Code     ← Vendor Code
  Vendor Name     ← Vendor Name

No joins, reconciliation logic, or calculations are performed here.
Each output row corresponds to exactly one row of the uploaded GRPO Report.
Remaining columns are set to None until subsequent phases add them.
"""

from __future__ import annotations

import pandas as pd

from app.cleaning import detect_columns
from app.analysis.calculated_fields import field, same_row


# All 14 display column keys used by the frontend table.
# Only the three mapped columns are populated in this phase.
_TABLE_COLUMNS = [
    "GRN No.",
    "Gate Entry No.",
    "Gate Entry Date",
    "GRN Date",
    "PO Number",
    "AP Invoice No.",
    "Vendor Code",
    "Vendor Name",
    "Vendor Country",
    "#Items",
    "GRN Value",
    "Days GE→GRN",
    "Within 2-day SLA",
    "GRN > 2 days (Breach)",
    "Seq Exception (GRN < GE)",
]

_EMPTY_RESULT = {
    "kpis":   {},
    "charts": {},
    "tables": [
        {"title": "GE to GRN Full Reconciliation List", "rows": []},
    ],
}


def _safe_str(val) -> str | None:
    """Return a stripped string value, or None for blank / NaN / null inputs."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    s = str(val).strip()
    # Preserve leading zeros; only discard values that carry no information
    if s.lower() in ("nan", "none", "nat", ""):
        return None
    return s


def _normalize_id(val) -> str:
    """Uppercase, strip trailing .0 — consistent with gate_entry.py normalize_id."""
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


def _seq_exception_grn_ge(raw_ge, raw_grn) -> int | None:
    """Return 1 if Gate Entry date is strictly later than GRN date, 0 if equal or earlier, None if either is missing/invalid."""
    if raw_ge is None or raw_grn is None:
        return None
    try:
        d_ge  = pd.to_datetime(raw_ge,  errors="coerce", dayfirst=True)
        d_grn = pd.to_datetime(raw_grn, errors="coerce", dayfirst=True)
        if pd.isna(d_ge) or pd.isna(d_grn):
            return None
        return 1 if d_ge > d_grn else 0
    except Exception:
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


def _calc_days(raw_from, raw_to) -> int | None:
    """Return integer calendar days (raw_to − raw_from) using datetime objects.
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

    # ── GRPO Report column detection ─────────────────────────────────────────
    # detect_columns resolves headers case-insensitively via config.py aliases.
    #   grpo_no      → "GRPO No", "Receipt No", "GRN No", …
    #   ge_no        → "Gate Entry No", "GE No", "Security Entry No", …
    #   po_no        → "PO Number", "PO No", "Purchase Order No", …
    #   vendor_code  → "Vendor Code", "BP Code", "Supplier Code", …
    #   vendor_name  → "Vendor Name", "BP Name", "Supplier Name", …
    #   posting_date → "Document Date", "Posting Date", "Doc Date", …  (GRN Date)
    #   grpo_date    → "GRPO Date", "Receipt Date", …                  (GRN Date fallback)
    grpo_map        = detect_columns(df_grpo)
    col_grn         = grpo_map.get("grpo_no")
    col_ge          = grpo_map.get("ge_no")
    col_po          = grpo_map.get("po_no")
    col_vendor_code = grpo_map.get("vendor_code")
    col_vendor_name = grpo_map.get("vendor_name")
    # GRN Date must come from "Document Date" when that column exists.
    # detect_columns resolves posting_date to "Posting Date" before "Document Date"
    # (alias order in config.py), so we check for the exact header first.
    _doc_date_col = next(
        (c for c in df_grpo.columns if c.strip().lower() == "document date"),
        None,
    )
    col_grpo_date    = _doc_date_col or grpo_map.get("posting_date") or grpo_map.get("grpo_date")
    col_line_total   = grpo_map.get("line_total")
    col_po_qty       = grpo_map.get("po_qty")

    col_doc_currency = next(
        (c for c in df_grpo.columns if c.strip().lower() == "document currency"),
        None,
    )

    # ── AP Invoice Report: build GRPO No. → AP Invoice No. lookup ────────────
    # Join key: GRPO's GRPO No. ↔ AP Invoice Report's GRPO Number column.
    # inv_no_lookup: { normalized_grpo_no: ap_invoice_no_str | None }
    inv_no_lookup: dict[str, str | None] = {}
    df_ap = dfs.get("ap_invoice_report")
    if df_ap is None:
        df_ap = dfs.get("purchase_register")
    if df_ap is not None and not df_ap.empty:
        ap_map      = detect_columns(df_ap)
        col_ap_grpo = ap_map.get("grpo_no")
        col_ap_inv  = ap_map.get("invoice_no")
        if col_ap_grpo and col_ap_inv:
            for _, ap_row in df_ap.iterrows():
                grpo_key = _normalize_id(ap_row[col_ap_grpo])
                if grpo_key and grpo_key not in inv_no_lookup:  # first match per GRPO No. wins
                    inv_no_lookup[grpo_key] = _safe_str(ap_row[col_ap_inv])

    # ── Gate Entry Report: build GE No. → GE Date lookup ─────────────────────
    # Gate Entry Date lives in the Gate Entry Report, not in the GRPO Report.
    # We join on Gate Entry No. (already present in each GRPO row).
    ge_date_lookup: dict[str, str | None] = {}
    ge_raw_lookup:  dict[str, object]     = {}   # raw cell value for datetime arithmetic
    df_ge = dfs.get("gate_entry")
    if df_ge is not None and not df_ge.empty:
        ge_map          = detect_columns(df_ge)
        col_ge_rep_no   = ge_map.get("ge_no")    # "Gate Entry No" in GE Report
        col_ge_rep_date = ge_map.get("ge_date")  # "Gate Entry Date" / "GE Date"
        if col_ge_rep_no and col_ge_rep_date:
            for _, ge_row in df_ge.iterrows():
                key = _normalize_id(ge_row[col_ge_rep_no])
                if key and key not in ge_date_lookup:   # keep first match per GE No.
                    ge_date_lookup[key] = _fmt_date(ge_row[col_ge_rep_date])
                    ge_raw_lookup[key]  = ge_row[col_ge_rep_date]

    # ── Build one output row per GRPO Report row ──────────────────────────────
    rows = []
    for _, grpo_row in df_grpo.iterrows():
        # Gate Entry Date lookup: normalize the GE No. from this GRPO row,
        # then find the corresponding date in the Gate Entry Report.
        grn_key    = _normalize_id(grpo_row[col_grn]) if col_grn else ""
        ge_no_key  = _normalize_id(grpo_row[col_ge]) if col_ge else ""
        ge_date    = ge_date_lookup.get(ge_no_key)   # None when no match
        ge_raw     = ge_raw_lookup.get(ge_no_key)    # raw value for day calculation
        grn_raw    = grpo_row[col_grpo_date] if col_grpo_date else None
        days_ge_grn = _calc_days(ge_raw, grn_raw)

        rows.append({
            "GRN No.":               _safe_str(grpo_row[col_grn])         if col_grn         else None,
            "Gate Entry No.":        _safe_str(grpo_row[col_ge])          if col_ge          else None,
            "Gate Entry Date":       ge_date,
            "GRN Date":              _fmt_date(grpo_row[col_grpo_date])   if col_grpo_date   else None,
            "PO Number":             _safe_str(grpo_row[col_po])          if col_po          else None,
            "AP Invoice No.":        inv_no_lookup.get(grn_key),
            "Vendor Code":           _safe_str(grpo_row[col_vendor_code]) if col_vendor_code else None,
            "Vendor Name":           _safe_str(grpo_row[col_vendor_name]) if col_vendor_name else None,
            "Vendor Country":        "India" if col_doc_currency and str(grpo_row[col_doc_currency]).strip().upper() == "INR" else ("USA" if col_doc_currency else None),
            "#Items":                _safe_int(grpo_row[col_po_qty]) if col_po_qty else None,
            "GRN Value":             _safe_num(grpo_row[col_line_total]) if col_line_total else None,
            "Days GE→GRN":           days_ge_grn,
            "Within 2-day SLA":      (1 if days_ge_grn <= 2 else 0) if days_ge_grn is not None else None,
            "GRN > 2 days (Breach)": (1 if days_ge_grn >  2 else 0) if days_ge_grn is not None else None,
            "Seq Exception (GRN < GE)": _seq_exception_grn_ge(ge_raw, grn_raw),
        })

    # ── KPI computations from reconciliation rows ─────────────────────────────
    days_vals   = [r["Days GE→GRN"]             for r in rows if r["Days GE→GRN"]             is not None]
    sla_vals    = [r["Within 2-day SLA"]         for r in rows if r["Within 2-day SLA"]         is not None]
    breach_vals = [r["GRN > 2 days (Breach)"]    for r in rows if r["GRN > 2 days (Breach)"]    is not None]
    seq_vals    = [r["Seq Exception (GRN < GE)"]  for r in rows if r["Seq Exception (GRN < GE)"]  is not None]

    within_sla  = sum(sla_vals)
    breach      = sum(breach_vals)
    denominator = within_sla + breach
    sla_pct     = f"{within_sla / denominator * 100:.1f}%" if denominator else "—"

    flagged = [
        r for r in rows
        if r.get("GRN > 2 days (Breach)") == 1 or r.get("Seq Exception (GRN < GE)") == 1
    ]

    kpis = {
        "grns_with_gate_entry":   len({r["GRN No."] for r in rows if r.get("Gate Entry No.") not in (None, "")}),
        "within_2_day_sla":       within_sla,
        "breach_gt_2_days":       breach,
        "sla_compliance_pct":     sla_pct,
        "avg_days_ge_to_grn":     round(sum(days_vals) / len(days_vals), 2) if days_vals else None,
        "max_days_ge_to_grn":     max(days_vals) if days_vals else None,
        "sequence_exceptions":    sum(seq_vals),
        "unique_po_numbers":      len({r["PO Number"]    for r in rows if r.get("PO Number")    not in (None, "")}),
        "unique_grn_nos":         len({r["GRN No."]      for r in rows if r.get("GRN No.")      not in (None, "")}),
        "unique_ap_invoices":     len({r["AP Invoice No."] for r in rows if r.get("AP Invoice No.") not in (None, "")}),
        "unique_ap_credit_notes": 0,
        "unique_pos_flagged":     len({r["PO Number"] for r in flagged if r.get("PO Number") not in (None, "")}),
        "unique_grns_flagged":    len({r["GRN No."]   for r in flagged if r.get("GRN No.")   not in (None, "")}),
    }

    return {
        "kpis":   kpis,
        "charts": {},
        "tables": [
            {
                "title": "GE to GRN Full Reconciliation List",
                "rows": rows,
                "calculated_fields": {
                    "Days GE→GRN": field(
                        "GRN Date − Gate Entry Date",
                        "ABS(GRN_Date − Gate_Entry_Date)",
                        inputs=[
                            {"field": "Gate Entry Date", "source_file": "Gate Entry Report", "source_record": "Gate Entry No."},
                            {"field": "GRN Date", "source_file": "GRPO Report", "source_record": "GRN No."},
                        ],
                    ),
                    "Within 2-day SLA": field(
                        "Days GE→GRN ≤ 2 days",
                        "IF(Days_GE_GRN ≤ 2, 1, 0)",
                        inputs=[{"field": "Days GE→GRN", "source_file": "GRPO Report (calculated)", "source_record": "GRN No."}],
                    ),
                    "GRN > 2 days (Breach)": field(
                        "Days GE→GRN > 2 days",
                        "IF(Days_GE_GRN > 2, 1, 0)",
                        inputs=[{"field": "Days GE→GRN", "source_file": "GRPO Report (calculated)", "source_record": "GRN No."}],
                    ),
                    "Seq Exception (GRN < GE)": field(
                        "Gate Entry Date > GRN Date",
                        "IF(Gate_Entry_Date > GRN_Date, 1, 0)",
                        inputs=[
                            {"field": "Gate Entry Date", "source_file": "Gate Entry Report", "source_record": "Gate Entry No."},
                            {"field": "GRN Date", "source_file": "GRPO Report", "source_record": "GRN No."},
                        ],
                    ),
                },
            },
        ],
    }
