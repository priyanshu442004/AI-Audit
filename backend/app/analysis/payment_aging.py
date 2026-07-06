"""
Module G — Payment Aging.

Days Late = Payment Date - Due Date  (negative = early)
Buckets:
  Early       : days < 0
  On-Time     : days == 0
  Not-Due     : payment_date is null, due_date in future
  Late        : 1 ≤ days ≤ 30   (paid but late)
  Overdue 0-30: unpaid, due 0-30 days ago
  Overdue 31-60
  Overdue 61-90
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import date

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_dates, parse_numeric
from app.analysis.calculated_fields import field, same_row


REQUIRED = ["invoice_no", "invoice_date", "due_date", "invoice_amount"]


def run(df_raw: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> dict:
    mapping = require_columns(df_raw, REQUIRED, "Purchase Register")
    for opt in ["payment_date", "vendor_code", "vendor_name", "pr_po_no",
                "posting_date"]:
        m2 = detect_columns(df_raw)
        if opt in m2:
            mapping[opt] = m2[opt]

    df = rename_canonical(df_raw, mapping).copy()
    # invoice_date might come through as posting_date alias
    if "invoice_date" not in df.columns and "posting_date" in df.columns:
        df = df.rename(columns={"posting_date": "invoice_date"})
    df["invoice_date"]    = parse_dates(df["invoice_date"])
    df["due_date"]        = parse_dates(df["due_date"])
    df["invoice_amount"]  = parse_numeric(df["invoice_amount"]).fillna(0)

    if "payment_date" in df.columns:
        df["payment_date"] = parse_dates(df["payment_date"])
    else:
        df["payment_date"] = pd.NaT

    today = reference_date or pd.Timestamp.today().normalize()

    # Effective payment/comparison date
    df["eff_date"] = df["payment_date"].fillna(today)

    df["days_late"] = (df["eff_date"] - df["due_date"]).dt.days

    def bucket(row):
        d = row["days_late"]
        paid = pd.notna(row["payment_date"])
        if pd.isna(d):
            return "Not-Due"
        if not paid:
            # unpaid
            if d < 0:
                return "Not-Due"
            elif d <= 30:
                return "Overdue 0-30d"
            elif d <= 60:
                return "Overdue 31-60d"
            else:
                return "Overdue 61-90d"
        else:
            if d < 0:
                return "Early"
            elif d == 0:
                return "On-Time"
            else:
                return "Late"

    df["aging_bucket"] = df.apply(bucket, axis=1)

    bucket_order = ["Early", "On-Time", "Not-Due", "Late",
                    "Overdue 0-30d", "Overdue 31-60d", "Overdue 61-90d"]

    counts = df["aging_bucket"].value_counts()
    totals = df.groupby("aging_bucket")["invoice_amount"].sum()

    def _cnt(b): return int(counts.get(b, 0))
    def _amt(b): return round(totals.get(b, 0.0) / 1e5, 2)  # in Lakhs

    total_invoices = len(df)
    early_cnt  = _cnt("Early")
    on_time    = _cnt("On-Time")
    not_due    = _cnt("Not-Due")
    late       = _cnt("Late")
    ov030      = _cnt("Overdue 0-30d")
    ov3160     = _cnt("Overdue 31-60d")
    ov6190     = _cnt("Overdue 61-90d")
    overdue    = ov030 + ov3160 + ov6190
    overdue_amt_l = round((totals.get("Overdue 0-30d", 0) + totals.get("Overdue 31-60d", 0) + totals.get("Overdue 61-90d", 0)) / 1e5, 2)
    overdue_amt_cr = round(overdue_amt_l / 100, 4)
    on_time_pct = round((early_cnt + on_time) / total_invoices * 100, 1) if total_invoices else 0.0

    max_count = max(early_cnt, on_time, not_due, late, ov030, ov3160, ov6190, 1)
    bars = [
        {"label": "Early Payment",  "value": early_cnt,  "pct": round(early_cnt  / max_count * 100, 0), "color": "#22c55e"},
        {"label": "Late Payment",   "value": late,       "pct": round(late       / max_count * 100, 0), "color": "#f59e0b"},
        {"label": "Not Yet Due",    "value": not_due,    "pct": round(not_due    / max_count * 100, 0), "color": "#06b6d4"},
        {"label": "On-Time",        "value": on_time,    "pct": round(on_time    / max_count * 100, 0), "color": "#14b8a6"},
        {"label": "Overdue 0-30d",  "value": ov030,      "pct": round(ov030      / max_count * 100, 0), "color": "#f87171"},
        {"label": "Overdue 31-60d", "value": ov3160,     "pct": round(ov3160     / max_count * 100, 0), "color": "#ef4444"},
        {"label": "Overdue 61-90d", "value": ov6190,     "pct": round(ov6190     / max_count * 100, 0), "color": "#dc2626"},
    ]

    overdue_amt_bars = [
        {"label": "Overdue 0-30 days",  "value_l": _amt("Overdue 0-30d"),  "pct": round(_amt("Overdue 0-30d")  / overdue_amt_l * 100, 0) if overdue_amt_l else 0},
        {"label": "Overdue 31-60 days", "value_l": _amt("Overdue 31-60d"), "pct": round(_amt("Overdue 31-60d") / overdue_amt_l * 100, 0) if overdue_amt_l else 0},
        {"label": "Overdue 61-90 days", "value_l": _amt("Overdue 61-90d"), "pct": round(_amt("Overdue 61-90d") / overdue_amt_l * 100, 0) if overdue_amt_l else 0},
    ]

    # Detail table
    cols = ["invoice_no", "invoice_date", "due_date", "payment_date",
            "invoice_amount", "days_late", "aging_bucket"]
    if "vendor_code" in df.columns: cols.insert(1, "vendor_code")
    detail = df[[c for c in cols if c in df.columns]].copy()
    detail["invoice_amount"] = detail["invoice_amount"].round(2)
    detail = detail.rename(columns={
        "invoice_no": "Invoice No", "vendor_code": "Vendor Code",
        "invoice_date": "Invoice Date", "due_date": "Due Date",
        "payment_date": "Payment Date", "invoice_amount": "Amount (₹)",
        "days_late": "Days Late", "aging_bucket": "Aging Bucket",
    })

    overdue_detail = detail[detail["Aging Bucket"].str.startswith("Overdue")]

    def _rows(f):
        return f.fillna("").astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "total_invoices":  total_invoices,
            "early":           early_cnt,
            "on_time":         on_time,
            "late":            late,
            "not_due":         not_due,
            "overdue":         overdue,
            "overdue_amt_cr":  overdue_amt_cr,
            "overdue_amt_l":   overdue_amt_l,
            "on_time_pct":     on_time_pct,
        },
        "charts": {
            "aging_bars":      bars,
            "overdue_amt_bars": overdue_amt_bars,
        },
        "tables": [
            {
                "title": "Payment Aging – Overdue Invoices",
                "rows": _rows(overdue_detail.head(500)),
                "calculated_fields": {
                    "Days Late": field(
                        "Payment Date − Due Date",
                        "Payment_Date − Due_Date",
                        inputs=[
                            {"field": "Due Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                            {"field": "Payment Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                    "Aging Bucket": field(
                        "Categorise by Days Late and Payment Status",
                        "IF(Paid, IF(Days<0,'Early',IF(Days=0,'On-Time','Late')), IF(Days<0,'Not-Due','Overdue…'))",
                        inputs=[
                            {"field": "Days Late", "source_file": "Purchase Register (calculated)", "source_record": "Invoice No"},
                            {"field": "Payment Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                },
            },
            {
                "title": "Payment Aging – Full Invoice List",
                "rows": _rows(detail.head(500)),
                "calculated_fields": {
                    "Days Late": field(
                        "Payment Date − Due Date",
                        "Payment_Date − Due_Date",
                        inputs=[
                            {"field": "Due Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                            {"field": "Payment Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                    "Aging Bucket": field(
                        "Categorise by Days Late and Payment Status",
                        "IF(Paid, IF(Days<0,'Early',IF(Days=0,'On-Time','Late')), IF(Days<0,'Not-Due','Overdue…'))",
                        inputs=[
                            {"field": "Days Late", "source_file": "Purchase Register (calculated)", "source_record": "Invoice No"},
                            {"field": "Payment Date", "source_file": "Purchase Register", "source_record": "Invoice No"},
                        ],
                    ),
                },
            },
        ],
    }
