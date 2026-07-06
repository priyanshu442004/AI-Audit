"""
Module H — MSME Compliance (45-day rule).

MSMED Act §16: Micro & Small enterprises must be paid within 45 days.
Breach if payment delay > 45 days.
Indicative penalty: 27% p.a. (3 × RBI Bank Rate 9%).
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_dates, parse_numeric
from app.config import MSME_PAYMENT_LIMIT_DAYS, MSME_PENALTY_RATE_PA


REQUIRED_PR = ["invoice_no", "invoice_date", "due_date", "invoice_amount"]
REQUIRED_VM = ["vendor_code", "msme_category"]
MSME_BREACH_CATS = {"micro", "small"}


def run(df_pr_raw: pd.DataFrame, df_vm_raw: pd.DataFrame,
        reference_date: pd.Timestamp | None = None) -> dict:
    # ── Purchase Register ────────────────────────────────────────────────────
    pr_map = require_columns(df_pr_raw, REQUIRED_PR, "Purchase Register")
    for opt in ["payment_date", "vendor_code", "posting_date"]:
        m2 = detect_columns(df_pr_raw)
        if opt in m2:
            pr_map[opt] = m2[opt]

    df_pr = rename_canonical(df_pr_raw, pr_map).copy()
    # invoice_date may have been claimed as posting_date
    if "invoice_date" not in df_pr.columns and "posting_date" in df_pr.columns:
        df_pr = df_pr.rename(columns={"posting_date": "invoice_date"})
    df_pr["invoice_date"]   = parse_dates(df_pr["invoice_date"])
    df_pr["due_date"]       = parse_dates(df_pr["due_date"])
    df_pr["invoice_amount"] = parse_numeric(df_pr["invoice_amount"]).fillna(0)
    if "payment_date" in df_pr.columns:
        df_pr["payment_date"] = parse_dates(df_pr["payment_date"])
    else:
        df_pr["payment_date"] = pd.NaT

    # ── Vendor Master ────────────────────────────────────────────────────────
    vm_map = require_columns(df_vm_raw, REQUIRED_VM, "Vendor Master")
    for opt in ["vendor_name"]:
        m2 = detect_columns(df_vm_raw)
        if opt in m2:
            vm_map[opt] = m2[opt]

    df_vm_renamed = rename_canonical(df_vm_raw, vm_map)
    df_vm = df_vm_renamed[
        [c for c in ["vendor_code", "vendor_name", "msme_category"]
         if c in df_vm_renamed.columns]
    ].copy()
    df_vm["msme_cat_norm"] = df_vm["msme_category"].astype(str).str.lower().str.strip()

    # ── Merge ────────────────────────────────────────────────────────────────
    if "vendor_code" in df_pr.columns and "vendor_code" in df_vm.columns:
        df = df_pr.merge(df_vm, on="vendor_code", how="left")
    elif "vendor_code" in df_pr.columns:
        df = df_pr.copy()
        df["msme_cat_norm"] = "n"
    else:
        df = df_pr.copy()
        df["msme_cat_norm"] = "n"  # unknown

    today = reference_date or pd.Timestamp.today().normalize()
    df["eff_pay_date"] = df["payment_date"].fillna(today)

    # Delay = effective payment date - due_date
    df["delay_days"] = (df["eff_pay_date"] - df["due_date"]).dt.days.round(0).astype("Int64")

    # 45-day rule applies only to Micro & Small
    df["is_msme_breach_eligible"] = df["msme_cat_norm"].isin(MSME_BREACH_CATS)
    df["breach"] = df["is_msme_breach_eligible"] & (df["delay_days"] > MSME_PAYMENT_LIMIT_DAYS)

    # Indicative penalty: principal × rate × days / 365
    df["penalty"] = np.where(
        df["breach"],
        df["invoice_amount"] * MSME_PENALTY_RATE_PA * df["delay_days"].astype(float) / 365,
        0.0,
    )

    # Category aggregates (all MSME + non)
    cat_map = {"micro": "MICRO", "small": "SMALL", "medium": "MEDIUM"}
    df["msme_cat_display"] = df["msme_cat_norm"].map(cat_map).fillna("N")

    cat_stats = (
        df.groupby("msme_cat_display")
        .agg(
            invoice_count=("invoice_no", "count"),
            total_value=("invoice_amount", "sum"),
            avg_delay=("delay_days", "mean"),
            breach_count=("breach", "sum"),
        )
        .reset_index()
        .rename(columns={"msme_cat_display": "MSME Category"})
    )

    micro_inv  = int(df[df["msme_cat_display"] == "MICRO"]["invoice_no"].count())
    small_inv  = int(df[df["msme_cat_display"] == "SMALL"]["invoice_no"].count())
    total_msme = micro_inv + small_inv
    msme_value_cr = round(
        df[df["msme_cat_norm"].isin(MSME_BREACH_CATS)]["invoice_amount"].sum() / 1e7, 2
    )

    breach_df     = df[df["breach"]].copy()
    breaches      = len(breach_df)
    breach_val_cr = round(breach_df["invoice_amount"].sum() / 1e7, 4)
    penalty_l     = round(breach_df["penalty"].sum() / 1e5, 2)
    breach_rate   = round(breaches / total_msme * 100, 1) if total_msme else 0.0

    # MSME donut: invoice count by category
    CIRC = 314.0
    total_inv = len(df)
    segs = []
    offset = 0
    colors = {"MEDIUM": "#6366f1", "MICRO": "#22c55e", "N": "#f59e0b", "SMALL": "#ef4444"}
    for cat in ["MEDIUM", "MICRO", "N", "SMALL"]:
        cnt = int((df["msme_cat_display"] == cat).sum())
        dash = round(cnt / total_inv * CIRC, 0) if total_inv else 0
        segs.append({"label": cat, "value": cnt, "dash": dash, "offset": -offset, "color": colors.get(cat, "#94a3b8")})
        offset += dash

    # Average delay bars per category
    avg_delay_bars = (
        cat_stats[["MSME Category", "avg_delay"]]
        .rename(columns={"avg_delay": "Avg Delay Days"})
        .assign(pct=lambda r: (r["Avg Delay Days"].abs() / r["Avg Delay Days"].abs().max() * 100).round(0))
    )

    # Breach detail
    breach_cols = ["invoice_no", "invoice_date", "due_date", "payment_date",
                   "invoice_amount", "delay_days", "penalty"]
    if "vendor_code" in breach_df.columns: breach_cols.insert(1, "vendor_code")
    if "vendor_name" in breach_df.columns: breach_cols.insert(2, "vendor_name")
    if "msme_cat_display" in breach_df.columns: breach_cols.append("msme_cat_display")
    breach_detail = breach_df[[c for c in breach_cols if c in breach_df.columns]].copy()
    breach_detail["invoice_amount"] = breach_detail["invoice_amount"].round(2)
    breach_detail["penalty"]        = breach_detail["penalty"].round(2)
    breach_detail = breach_detail.rename(columns={
        "invoice_no": "Invoice No", "vendor_code": "Vendor Code",
        "vendor_name": "Vendor Name", "invoice_date": "Invoice Date",
        "due_date": "Due Date", "payment_date": "Payment Date",
        "invoice_amount": "Invoice Amount (₹)", "delay_days": "Delay Days",
        "penalty": "Indicative Penalty (₹)", "msme_cat_display": "MSME Category",
    })

    # Summary by category
    cat_summary = cat_stats.copy()
    cat_summary["total_value"] = cat_summary["total_value"].round(2)
    cat_summary["avg_delay"]   = cat_summary["avg_delay"].round(1)
    cat_summary = cat_summary.rename(columns={
        "invoice_count": "Invoice Count", "total_value": "Total Value (₹)",
        "avg_delay": "Avg Delay (Days)", "breach_count": "Breach Count",
    })

    from app.analysis.calculated_fields import field, same_row

    def _rows(f):
        return f.fillna("").astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "micro_invoices":  micro_inv,
            "small_invoices":  small_inv,
            "total_msme":      total_msme,
            "msme_value_cr":   msme_value_cr,
            "breaches":        breaches,
            "breach_val_cr":   breach_val_cr,
            "penalty_l":       penalty_l,
            "breach_rate":     breach_rate,
        },
        "charts": {
            "msme_donut": {
                "total": total_inv,
                "segments": segs,
            },
            "avg_delay_bars": _rows(avg_delay_bars),
        },
        "tables": [
            {
                "title": "MSME 45-Day Breach Detail",
                "rows": _rows(breach_detail),
                "calculated_fields": {
                    "Delay Days": field(
                        "Payment Date − Due Date",
                        "Payment_Date − Due_Date",
                        inputs=[
                            {"field": "Due Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                            {"field": "Payment Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                    "Indicative Penalty (₹)": field(
                        "Invoice Amount × 27% × Delay Days ÷ 365",
                        "Invoice_Amount * 0.27 * Delay_Days / 365",
                        inputs=[
                            {"field": "Invoice Amount (₹)", "source_file": "Purchase Register", "source_record": "Invoice No"},
                            {"field": "Delay Days", "source_file": "Same row", "source_record": "Same row"},
                        ],
                    ),
                },
            },
            {"title": "MSME Summary by Registration Category","rows": _rows(cat_summary)},
        ],
    }
