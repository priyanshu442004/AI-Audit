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
    "Days GE→GRN",          # "Days GE→GRN"
    "Within 2-day SLA",
    "GRN > 2 days (Breach)",
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
    col_grpo_date = _doc_date_col or grpo_map.get("posting_date") or grpo_map.get("grpo_date")
    print("Detected GRN date column:", col_grpo_date, "(exact Document Date match)" if _doc_date_col else "(via alias fallback)")

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
        ge_no_key  = _normalize_id(grpo_row[col_ge]) if col_ge else ""
        ge_date    = ge_date_lookup.get(ge_no_key)   # None when no match
        ge_raw     = ge_raw_lookup.get(ge_no_key)    # raw value for day calculation
        grn_raw    = grpo_row[col_grpo_date] if col_grpo_date else None
        days_ge_grn = _calc_days(ge_raw, grn_raw)

        # ── DEBUG: inspect date columns for GRPO No. 252607146 ───────────────
        if _safe_str(grpo_row[col_grn] if col_grn else None) == "252607146":
            print("--- DEBUG GRPO 252607146 ---")
            print("  col_grpo_date (detected column name):", col_grpo_date)
            print("  value read from col_grpo_date:       ", grpo_row[col_grpo_date] if col_grpo_date else "N/A")
            posting_col = next((c for c in df_grpo.columns if str(c).strip().lower() == "posting date"), None)
            document_col = next((c for c in df_grpo.columns if str(c).strip().lower() == "document date"), None)
            print("  raw Posting Date column name:        ", posting_col)
            print("  raw Posting Date value:              ", grpo_row[posting_col] if posting_col else "column not found")
            print("  raw Document Date column name:       ", document_col)
            print("  raw Document Date value:             ", grpo_row[document_col] if document_col else "column not found")
            print("---------------------------")
        # ── END DEBUG ─────────────────────────────────────────────────────────

        rows.append({
            "GRN No.":               _safe_str(grpo_row[col_grn])         if col_grn         else None,
            "Gate Entry No.":        _safe_str(grpo_row[col_ge])          if col_ge          else None,
            "Gate Entry Date":       ge_date,
            "GRN Date":              _fmt_date(grpo_row[col_grpo_date])   if col_grpo_date   else None,
            "PO Number":             _safe_str(grpo_row[col_po])          if col_po          else None,
            "AP Invoice No.":        None,
            "Vendor Code":           _safe_str(grpo_row[col_vendor_code]) if col_vendor_code else None,
            "Vendor Name":           _safe_str(grpo_row[col_vendor_name]) if col_vendor_name else None,
            "Vendor Country":        None,
            "#Items":                None,
            "GRN Value":             None,
            "Days GE→GRN":           days_ge_grn,
            "Within 2-day SLA":      (1 if days_ge_grn <= 2 else 0) if days_ge_grn is not None else None,
            "GRN > 2 days (Breach)": (1 if days_ge_grn >  2 else 0) if days_ge_grn is not None else None,
        })

    return {
        "kpis":   {},
        "charts": {},
        "tables": [
            {"title": "GE to GRN Full Reconciliation List", "rows": rows},
        ],
    }
