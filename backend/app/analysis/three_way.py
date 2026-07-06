"""
Module J — 3-Way Matching.

Reconcile PO ↔ GRPO ↔ Invoice on Qty and Price within 5% tolerance.
Categories:
  Perfect Match       : qty AND price both within 5%
  Match with Variance : at least one within 5%, other not
  Missing Invoice Link: GRPO has no AP invoice
  Missing PO Link     : GRPO has no backing PO
  No PO + No Invoice  : GRPO with neither
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_numeric
from app.config import VARIANCE_TOLERANCE_PCT
from app.analysis.calculated_fields import field, same_row


REQUIRED_PO   = ["po_no", "item_code", "po_qty"]  # unit_price detected with fallback
REQUIRED_GRPO = ["grpo_no", "grpo_base_po", "item_code", "grpo_qty", "grpo_rate"]
REQUIRED_PR   = ["invoice_no", "pr_po_no", "invoice_amount"]


def _pct_diff(a, b):
    """Absolute % difference between a and b relative to max(a,b)."""
    denom = np.where(np.maximum(a, b) > 0, np.maximum(a, b), np.nan)
    return np.abs(a - b) / denom * 100


def run(
    df_po_raw:   pd.DataFrame,
    df_grpo_raw: pd.DataFrame,
    df_pr_raw:   pd.DataFrame,
) -> dict:
    # ── PO ───────────────────────────────────────────────────────────────────
    po_map = require_columns(df_po_raw, REQUIRED_PO, "Purchase Order")
    for opt in ["vendor_code", "vendor_name"]:
        m2 = detect_columns(df_po_raw)
        if opt in m2:
            po_map[opt] = m2[opt]
    df_po = rename_canonical(df_po_raw, po_map).copy()
    df_po["po_qty"] = parse_numeric(df_po["po_qty"])
    if "unit_price" not in df_po.columns and "grpo_rate" in df_po.columns:
        df_po = df_po.rename(columns={"grpo_rate": "unit_price"})
    df_po["unit_price"] = parse_numeric(df_po["unit_price"])

    # PO line key = (po_no, item_code)
    df_po_keyed = df_po[["po_no", "item_code", "po_qty", "unit_price"]].copy()
    if "vendor_code" in df_po.columns:
        df_po_keyed["vendor_code"] = df_po["vendor_code"]

    # ── GRPO ─────────────────────────────────────────────────────────────────
    grpo_map = require_columns(df_grpo_raw, ["grpo_no", "item_code", "grpo_qty"], "GRPO")
    for opt in ["grpo_base_po", "po_no", "grpo_rate", "unit_price"]:
        m2 = detect_columns(df_grpo_raw)
        if opt in m2:
            grpo_map[opt] = m2[opt]
    df_grpo = rename_canonical(df_grpo_raw, grpo_map).copy()
    if "grpo_base_po" not in df_grpo.columns and "po_no" in df_grpo.columns:
        df_grpo = df_grpo.rename(columns={"po_no": "grpo_base_po"})
    if "grpo_base_po" not in df_grpo.columns:
        df_grpo["grpo_base_po"] = None
    if "grpo_rate" not in df_grpo.columns and "unit_price" in df_grpo.columns:
        df_grpo = df_grpo.rename(columns={"unit_price": "grpo_rate"})
    if "grpo_rate" not in df_grpo.columns:
        df_grpo["grpo_rate"] = 0
    df_grpo["grpo_qty"]  = parse_numeric(df_grpo["grpo_qty"])
    df_grpo["grpo_rate"] = parse_numeric(df_grpo["grpo_rate"])

    # ── Purchase Register ─────────────────────────────────────────────────────
    pr_map = require_columns(df_pr_raw, ["invoice_no", "invoice_amount"], "Purchase Register")
    for opt in ["pr_po_no", "po_no", "invoice_date", "vendor_code"]:
        m2 = detect_columns(df_pr_raw)
        if opt in m2:
            pr_map[opt] = m2[opt]
    df_pr = rename_canonical(df_pr_raw, pr_map).copy()
    # pr_po_no may actually be po_no (if "PO No" was claimed by po_no last-wins)
    if "pr_po_no" not in df_pr.columns and "po_no" in df_pr.columns:
        df_pr = df_pr.rename(columns={"po_no": "pr_po_no"})
    df_pr["invoice_amount"] = parse_numeric(df_pr["invoice_amount"]).fillna(0)

    if "pr_po_no" not in df_pr.columns:
        df_pr["pr_po_no"] = None

    # Explode pr_po_no if it has comma separated values to correctly aggregate invoice amounts per PO
    df_pr_exploded = df_pr.copy()
    if "pr_po_no" in df_pr_exploded.columns:
        df_pr_exploded["pr_po_no"] = df_pr_exploded["pr_po_no"].fillna("").astype(str).apply(
            lambda x: [p.strip() for p in x.split(",") if p.strip()] if x else [None]
        )
        df_pr_exploded = df_pr_exploded.explode("pr_po_no")
        def clean_po(val):
            if val is None:
                return None
            v = str(val).strip()
            if v.endswith(".0"):
                v = v[:-2]
            return v
        df_pr_exploded["pr_po_no"] = df_pr_exploded["pr_po_no"].apply(clean_po)

    # Aggregate invoice amount per PO
    pr_by_po = (
        df_pr_exploded.groupby("pr_po_no", dropna=False)["invoice_amount"]
        .sum()
        .reset_index()
        .rename(columns={"pr_po_no": "po_no", "invoice_amount": "inv_amount"})
    )
    invoiced_pos = set(df_pr_exploded["pr_po_no"].dropna().astype(str).str.strip())

    # ── Merge GRPO → PO ───────────────────────────────────────────────────────
    merged = df_grpo.merge(
        df_po_keyed,
        left_on=["grpo_base_po", "item_code"],
        right_on=["po_no", "item_code"],
        how="left",
        suffixes=("_grpo", "_po"),
    )
    merged = merged.merge(pr_by_po, left_on="grpo_base_po", right_on="po_no",
                          how="left", suffixes=("", "_pr"))

    has_po  = merged["po_qty"].notna()
    has_inv = merged["grpo_base_po"].astype(str).str.strip().isin(invoiced_pos)

    # Qty & price variances
    merged["qty_var_pct"]   = _pct_diff(merged["grpo_qty"].fillna(0), merged["po_qty"].fillna(0))
    merged["price_var_pct"] = _pct_diff(merged["grpo_rate"].fillna(0), merged["unit_price"].fillna(0))

    tol = VARIANCE_TOLERANCE_PCT
    merged["qty_ok"]   = merged["qty_var_pct"]   <= tol
    merged["price_ok"] = merged["price_var_pct"] <= tol

    def classify(row):
        if not has_po[row.name] and not has_inv[row.name]:
            return "No PO + No Invoice"
        if not has_po[row.name]:
            return "Missing PO Link"
        if not has_inv[row.name]:
            return "Missing Invoice Link"
        if row["qty_ok"] and row["price_ok"]:
            return "Perfect Match"
        return "Match with Variance"

    merged["match_status"] = merged.apply(classify, axis=1)

    counts = merged["match_status"].value_counts().to_dict()

    def _cnt(k): return int(counts.get(k, 0))

    total        = len(merged)
    perfect      = _cnt("Perfect Match")
    with_var     = _cnt("Match with Variance")
    no_inv_link  = _cnt("Missing Invoice Link")
    no_po_link   = _cnt("Missing PO Link")
    no_both      = _cnt("No PO + No Invoice")

    # Donut
    CIRC = 314.0
    seg_order = [
        ("Match with Variance", "#6366f1"), ("No PO + No Invoice", "#f59e0b"),
        ("Missing Invoice Link", "#ef4444"), ("Perfect Match", "#22c55e"),
        ("Missing PO Link", "#94a3b8"),
    ]
    segments = []
    offset = 0
    for label, color in seg_order:
        v = _cnt(label)
        dash = round(v / total * CIRC, 0) if total else 0
        segments.append({"label": label, "value": v, "dash": dash,
                          "offset": -offset, "color": color})
        offset += dash

    # PO vs GRPO quantity comparison
    has_both = merged[has_po]
    po_gt_grpo = int((has_both["po_qty"] > has_both["grpo_qty"]).sum())
    po_lt_grpo = int((has_both["po_qty"] < has_both["grpo_qty"]).sum())
    po_eq_grpo = int((has_both["po_qty"] == has_both["grpo_qty"]).sum())
    total_po_qty   = float(has_both["po_qty"].sum())
    total_grpo_qty = float(has_both["grpo_qty"].sum())
    short_receipt  = total_po_qty - total_grpo_qty

    # Vendor mismatch summary
    if "vendor_code" in merged.columns:
        vendor_mm = (
            merged.groupby("vendor_code")
            .agg(
                records=("grpo_no", "count"),
                mismatches=("match_status", lambda s: (s != "Perfect Match").sum()),
            )
            .reset_index()
        )
        if "vendor_name" in df_po.columns:
            vendor_mm = vendor_mm.merge(
                df_po[["vendor_code", "vendor_name"]].drop_duplicates("vendor_code"),
                on="vendor_code", how="left",
            )
        vendor_mm["pct_mismatch"] = (vendor_mm["mismatches"] / vendor_mm["records"] * 100).round(1)
        vendor_mm = vendor_mm.sort_values("mismatches", ascending=False).head(20)
        vendor_mm = vendor_mm.rename(columns={
            "vendor_code": "Vendor Code", "vendor_name": "Vendor Name",
            "records": "Records", "mismatches": "Mismatches",
            "pct_mismatch": "% Mismatch",
        })
    else:
        vendor_mm = pd.DataFrame()

    # Detail table
    detail_cols = ["grpo_no", "grpo_base_po", "item_code",
                   "grpo_qty", "po_qty", "grpo_rate", "unit_price",
                   "qty_var_pct", "price_var_pct", "match_status"]
    if "vendor_code" in merged.columns:
        detail_cols.insert(1, "vendor_code")
    detail = merged[[c for c in detail_cols if c in merged.columns]].copy()
    for col in ["qty_var_pct", "price_var_pct"]:
        if col in detail.columns:
            detail[col] = detail[col].round(2)
    detail = detail.rename(columns={
        "grpo_no": "GRPO No", "grpo_base_po": "PO No", "item_code": "Item Code",
        "vendor_code": "Vendor Code", "grpo_qty": "GRPO Qty", "po_qty": "PO Qty",
        "grpo_rate": "GRPO Rate", "unit_price": "PO Rate",
        "qty_var_pct": "Qty Var %", "price_var_pct": "Price Var %",
        "match_status": "Match Status",
    })

    # 3-way summary table (match categories)
    summary_rows = [
        {"Category": k, "Count": _cnt(k), "% of Total": round(_cnt(k) / total * 100, 1) if total else 0}
        for k, _ in seg_order
    ]
    summary_df = pd.DataFrame(summary_rows)

    def _rows(f):
        return f.fillna("").astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "total_records":   total,
            "fully_matched":   perfect,
            "qty_exceptions":  with_var + no_inv_link + no_po_link,
            "rate_exceptions": with_var,
        },
        "charts": {
            "match_donut": {"total": total, "segments": segments},
            "po_vs_grpo": {
                "matched":        po_eq_grpo,
                "po_gt_grpo":     po_gt_grpo,
                "po_lt_grpo":     po_lt_grpo,
                "total_po_qty":   round(total_po_qty, 0),
                "total_grpo_qty": round(total_grpo_qty, 0),
                "short_receipt":  round(short_receipt, 0),
            },
        },
        "tables": [
            {"title": "Three-Way Match Summary Table",          "rows": _rows(summary_df)},
            {"title": "Top Matching Exceptions by Vendor",      "rows": _rows(vendor_mm)},
            {
                "title": "3-Way Match – Full Transaction Detail",
                "rows": _rows(detail.head(500)),
                "calculated_fields": {
                    "Qty Var %": field(
                        "|GRPO Qty − PO Qty| ÷ MAX(GRPO Qty, PO Qty) × 100",
                        "ABS(GRPO_Qty − PO_Qty) / MAX(GRPO_Qty, PO_Qty) * 100",
                        inputs=[
                            {"field": "GRPO Qty", "source_file": "GRPO Report", "source_record": "GRPO No"},
                            {"field": "PO Qty", "source_file": "Purchase Order", "source_record": "PO No"},
                        ],
                    ),
                    "Price Var %": field(
                        "|GRPO Rate − PO Rate| ÷ MAX(GRPO Rate, PO Rate) × 100",
                        "ABS(GRPO_Rate − PO_Rate) / MAX(GRPO_Rate, PO_Rate) * 100",
                        inputs=[
                            {"field": "GRPO Rate", "source_file": "GRPO Report", "source_record": "GRPO No"},
                            {"field": "PO Rate", "source_file": "Purchase Order", "source_record": "PO No"},
                        ],
                    ),
                    "Match Status": field(
                        "Categorise by Qty Var %, Price Var %, PO/Invoice links",
                        "IF(No_PO,'Missing PO Link',IF(No_Inv,'Missing Invoice Link',IF(Qty≤5% AND Price≤5%,'Perfect','Match with Variance')))",
                        inputs=[
                            {"field": "Qty Var %", "source_file": "GRPO Report (calculated)", "source_record": "GRPO No"},
                            {"field": "Price Var %", "source_file": "GRPO Report (calculated)", "source_record": "GRPO No"},
                            {"field": "PO No", "source_file": "Purchase Order", "source_record": "PO No"},
                            {"field": "AP Invoice", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                },
            },
        ],
    }
