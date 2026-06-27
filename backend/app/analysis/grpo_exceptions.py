"""
Module — GRPO / Gate-Entry / Invoice Linkage Exceptions.

- GRPO without Invoice
- Gate Entry without GRPO
- Invoice without Gate Entry (proxy: invoice not linked to a GE)
"""

from __future__ import annotations

import pandas as pd

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_dates


REQUIRED_GRPO = ["grpo_no"]
REQUIRED_GE   = ["ge_no"]
REQUIRED_PR   = ["invoice_no"]


def run(
    df_grpo_raw: pd.DataFrame,
    df_ge_raw:   pd.DataFrame,
    df_pr_raw:   pd.DataFrame,
) -> dict:
    # ── GRPO ─────────────────────────────────────────────────────────────────
    grpo_map = require_columns(df_grpo_raw, REQUIRED_GRPO, "GRPO")
    for opt in ["vendor_code", "grpo_date", "gate_entry_no", "grpo_base_po",
                "grpo_qty", "grpo_amount"]:
        m2 = detect_columns(df_grpo_raw)
        if opt in m2:
            grpo_map[opt] = m2[opt]
    df_grpo = rename_canonical(df_grpo_raw, grpo_map).copy()
    if "grpo_date" in df_grpo.columns:
        df_grpo["grpo_date"] = parse_dates(df_grpo["grpo_date"])

    # ── Gate Entry ────────────────────────────────────────────────────────────
    ge_map = require_columns(df_ge_raw, REQUIRED_GE, "Gate Entry")
    for opt in ["ge_grpo_no", "ge_date", "vendor_code"]:
        m2 = detect_columns(df_ge_raw)
        if opt in m2:
            ge_map[opt] = m2[opt]
    df_ge = rename_canonical(df_ge_raw, ge_map).copy()

    # ── Purchase Register ─────────────────────────────────────────────────────
    pr_map = require_columns(df_pr_raw, REQUIRED_PR, "Purchase Register")
    for opt in ["vendor_code", "invoice_date", "invoice_amount", "pr_po_no", "po_no"]:
        m2 = detect_columns(df_pr_raw)
        if opt in m2:
            pr_map[opt] = m2[opt]
    df_pr = rename_canonical(df_pr_raw, pr_map).copy()
    if "pr_po_no" not in df_pr.columns and "po_no" in df_pr.columns:
        df_pr = df_pr.rename(columns={"po_no": "pr_po_no"})
    if "invoice_date" in df_pr.columns:
        df_pr["invoice_date"] = parse_dates(df_pr["invoice_date"])

    # ── Exception 1: GRPO without Invoice ────────────────────────────────────
    # Use GE gate_entry_no if available to link GRPO→GE→PR
    grpo_nos = set(df_grpo["grpo_no"].dropna().astype(str).str.strip())

    # Try to find invoices linked to GRPO via purchase register PO ref
    if "pr_po_no" in df_pr.columns and "grpo_base_po" in df_grpo.columns:
        invoiced_pos = set()
        for po_val in df_pr["pr_po_no"].dropna().astype(str):
            for part in po_val.split(","):
                part_clean = part.strip()
                if part_clean.endswith(".0"):
                    part_clean = part_clean[:-2]
                if part_clean:
                    invoiced_pos.add(part_clean)
        
        # Clean grpo_base_po and check in invoiced_pos
        def clean_po(val):
            if pd.isna(val) or val is None:
                return ""
            v = str(val).strip()
            if v.endswith(".0"):
                v = v[:-2]
            return v
            
        grpo_base_po_cleaned = df_grpo["grpo_base_po"].apply(clean_po)
        grpo_no_inv  = df_grpo[~grpo_base_po_cleaned.isin(invoiced_pos)]
    else:
        grpo_no_inv = df_grpo.head(0)  # cannot determine

    grpo_no_inv_cnt = len(grpo_no_inv)

    # ── Exception 2: Gate Entry without GRPO ─────────────────────────────────
    if "ge_grpo_no" in df_ge.columns:
        ge_no_grpo = df_ge[
            ~df_ge["ge_grpo_no"].astype(str).str.strip().isin(grpo_nos)
        ]
    else:
        ge_no_grpo = df_ge.head(0)

    ge_no_grpo_cnt = len(ge_no_grpo)

    # ── Exception 3: Invoice without Gate Entry ───────────────────────────────
    # invoices where their PO is not referenced by any GE
    ge_grpo_nos = set()
    if "ge_grpo_no" in df_ge.columns:
        ge_grpo_nos = set(df_ge["ge_grpo_no"].dropna().astype(str).str.strip())

    if "pr_po_no" in df_pr.columns and "grpo_base_po" in df_grpo.columns:
        # GRPOs linked to a GE
        grpo_with_ge = df_grpo[df_grpo["grpo_no"].astype(str).str.strip().isin(ge_grpo_nos)]
        def clean_po(val):
            if pd.isna(val) or val is None:
                return ""
            v = str(val).strip()
            if v.endswith(".0"):
                v = v[:-2]
            return v
        po_with_ge   = set(grpo_with_ge["grpo_base_po"].apply(clean_po).dropna().unique())
        
        # Check if any of the comma separated POs in pr_po_no is in po_with_ge
        def has_ge_link(po_val):
            if pd.isna(po_val):
                return False
            for p in str(po_val).split(","):
                p_clean = p.strip()
                if p_clean.endswith(".0"):
                    p_clean = p_clean[:-2]
                if p_clean in po_with_ge:
                    return True
            return False
            
        mask = df_pr["pr_po_no"].apply(has_ge_link)
        inv_no_ge = df_pr[~mask]
    else:
        inv_no_ge = df_pr.head(0)

    inv_no_ge_cnt = len(inv_no_ge)
    total_exc     = grpo_no_inv_cnt + ge_no_grpo_cnt + inv_no_ge_cnt

    # Donut
    CIRC = 314.0
    grpo_dash = round(grpo_no_inv_cnt / total_exc * CIRC, 0) if total_exc else 0
    ge_dash   = round(ge_no_grpo_cnt  / total_exc * CIRC, 0) if total_exc else 0
    inv_dash  = round(inv_no_ge_cnt   / total_exc * CIRC, 0) if total_exc else 0

    # Build output tables
    grpo_no_inv_tbl = grpo_no_inv[[c for c in ["grpo_no", "vendor_code", "grpo_date", "grpo_base_po"] if c in grpo_no_inv.columns]].copy()
    grpo_no_inv_tbl = grpo_no_inv_tbl.rename(columns={
        "grpo_no": "GRPO No", "vendor_code": "Vendor Code",
        "grpo_date": "GRPO Date", "grpo_base_po": "Base PO",
    })

    ge_no_grpo_tbl = ge_no_grpo[[c for c in ["ge_no", "vendor_code", "ge_date", "ge_grpo_no"] if c in ge_no_grpo.columns]].copy()
    ge_no_grpo_tbl = ge_no_grpo_tbl.rename(columns={
        "ge_no": "GE No", "vendor_code": "Vendor Code",
        "ge_date": "GE Date", "ge_grpo_no": "Linked GRPO",
    })

    inv_no_ge_cols = ["invoice_no"]
    if "vendor_code" in inv_no_ge.columns: inv_no_ge_cols.append("vendor_code")
    if "invoice_date"   in inv_no_ge.columns: inv_no_ge_cols.append("invoice_date")
    if "invoice_amount" in inv_no_ge.columns: inv_no_ge_cols.append("invoice_amount")
    inv_no_ge_tbl = inv_no_ge[inv_no_ge_cols].copy()
    inv_no_ge_tbl = inv_no_ge_tbl.rename(columns={
        "invoice_no": "Invoice No", "vendor_code": "Vendor Code",
        "invoice_date": "Invoice Date", "invoice_amount": "Amount (₹)",
    })

    def _rows(f):
        return f.fillna("").astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "grpo_no_invoice":  grpo_no_inv_cnt,
            "ge_no_grpo":       ge_no_grpo_cnt,
            "invoice_no_ge":    inv_no_ge_cnt,
            "total_exceptions": total_exc,
        },
        "charts": {
            "exceptions_donut": {
                "total": total_exc,
                "segments": [
                    {"label": "GRPO without Invoice",      "value": grpo_no_inv_cnt, "dash": grpo_dash, "offset": 0,           "color": "#f59e0b"},
                    {"label": "Gate Entry without GRPO",   "value": ge_no_grpo_cnt,  "dash": ge_dash,   "offset": -grpo_dash,  "color": "#ef4444"},
                    {"label": "Invoice without Gate Entry","value": inv_no_ge_cnt,   "dash": inv_dash,  "offset": -(grpo_dash + ge_dash), "color": "#6366f1"},
                ],
            },
            "visual_distribution": [
                {"label": "Invoice without Gate Entry", "value": inv_no_ge_cnt,   "pct": round(inv_no_ge_cnt   / total_exc * 100, 0) if total_exc else 0},
                {"label": "GRPO without Invoice",       "value": grpo_no_inv_cnt, "pct": round(grpo_no_inv_cnt / total_exc * 100, 0) if total_exc else 0},
                {"label": "Gate Entry without GRPO",    "value": ge_no_grpo_cnt,  "pct": round(ge_no_grpo_cnt  / total_exc * 100, 0) if total_exc else 0},
            ],
        },
        "tables": [
            {"title": "GRPO without Invoice",         "rows": _rows(grpo_no_inv_tbl.head(500))},
            {"title": "Gate Entry without GRPO",      "rows": _rows(ge_no_grpo_tbl.head(500))},
            {"title": "Invoice without Gate Entry",   "rows": _rows(inv_no_ge_tbl.head(500))},
        ],
    }
