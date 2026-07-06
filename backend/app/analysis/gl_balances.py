"""
Module F — GL Vendor Balances.

Net = Total Credit - Total Debit per vendor.
Outstanding = Net > 0 (we owe)
Fully Paid  = Net == 0
Advance     = Net < 0 (debit balance)
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_numeric
from app.analysis.calculated_fields import field, same_row


REQUIRED = ["vendor_code", "debit", "credit"]


def run(df_raw: pd.DataFrame) -> dict:
    mapping = require_columns(df_raw, REQUIRED, "General Ledger")
    for opt in ["vendor_name", "gl_date", "gl_ref", "trans_type"]:
        m2 = detect_columns(df_raw)
        if opt in m2:
            mapping[opt] = m2[opt]

    df = rename_canonical(df_raw, mapping).copy()
    df["debit"]  = parse_numeric(df["debit"]).fillna(0)
    df["credit"] = parse_numeric(df["credit"]).fillna(0)

    agg_cols = {"debit": "sum", "credit": "sum"}
    if "vendor_name" in df.columns:
        agg_cols["vendor_name"] = "first"

    vendor_bal = df.groupby("vendor_code").agg(agg_cols).reset_index()
    vendor_bal.rename(columns={"vendor_code": "Vendor Code"}, inplace=True)
    if "vendor_name" in vendor_bal.columns:
        vendor_bal.rename(columns={"vendor_name": "Vendor Name"}, inplace=True)

    vendor_bal["net_balance"] = vendor_bal["credit"] - vendor_bal["debit"]

    tol = 0.01  # floating point tolerance for "fully paid"
    vendor_bal["balance_type"] = vendor_bal["net_balance"].apply(
        lambda x: "Fully Paid" if abs(x) <= tol else ("Outstanding" if x > tol else "Advance/Debit")
    )

    outstanding = vendor_bal[vendor_bal["balance_type"] == "Outstanding"]
    fully_paid  = vendor_bal[vendor_bal["balance_type"] == "Fully Paid"]
    advance     = vendor_bal[vendor_bal["balance_type"] == "Advance/Debit"]

    total_vendors   = len(vendor_bal)
    outstanding_cnt = len(outstanding)
    fully_paid_cnt  = len(fully_paid)
    advance_cnt     = len(advance)

    outstanding_cr = round(outstanding["net_balance"].sum() / 1e7, 2)
    advance_cr     = round(abs(advance["net_balance"].sum()) / 1e7, 2)
    net_liability_cr = round((outstanding["net_balance"].sum() + advance["net_balance"].sum()) / 1e7, 2)

    # Donut: payment status by count
    CIRC = 314.0
    adv_dash  = round(advance_cnt  / total_vendors * CIRC, 0) if total_vendors else 0
    os_dash   = round(outstanding_cnt / total_vendors * CIRC, 0) if total_vendors else 0
    fp_dash   = round(fully_paid_cnt / total_vendors * CIRC, 0) if total_vendors else 0

    # Top 20 outstanding vendors
    top_os = outstanding.nlargest(20, "net_balance").copy()
    top_os["net_balance"] = top_os["net_balance"].round(2)
    top_os = top_os.rename(columns={"debit": "Total Debit", "credit": "Total Credit",
                                     "net_balance": "Net Balance (₹)"})

    # Full vendor balance table
    full_table = vendor_bal.sort_values("net_balance", ascending=False).copy()
    full_table["debit"]       = full_table["debit"].round(2)
    full_table["credit"]      = full_table["credit"].round(2)
    full_table["net_balance"] = full_table["net_balance"].round(2)
    full_table = full_table.rename(columns={
        "debit": "Total Debit", "credit": "Total Credit",
        "net_balance": "Net Balance (₹)", "balance_type": "Status",
    })

    def _rows(f):
        return f.fillna("").astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "outstanding_cnt":  outstanding_cnt,
            "fully_paid_cnt":   fully_paid_cnt,
            "advance_cnt":      advance_cnt,
            "total_vendors":    total_vendors,
            "outstanding_cr":   outstanding_cr,
            "advance_cr":       advance_cr,
            "net_liability_cr": net_liability_cr,
        },
        "charts": {
            "payment_status": {
                "total": total_vendors,
                "segments": [
                    {"label": "Advance/Debit", "value": advance_cnt,     "color": "#6366f1", "dash": adv_dash,  "offset": 0},
                    {"label": "Outstanding",   "value": outstanding_cnt, "color": "#f59e0b", "dash": os_dash,   "offset": -adv_dash},
                    {"label": "Fully Paid",    "value": fully_paid_cnt,  "color": "#22c55e", "dash": fp_dash,   "offset": -(adv_dash + os_dash)},
                ],
            },
            "amount_bars": [
                {"label": "Outstanding", "value_cr": outstanding_cr, "pct": round(outstanding_cr / (outstanding_cr + advance_cr) * 100, 0) if (outstanding_cr + advance_cr) else 0},
                {"label": "Advance",     "value_cr": advance_cr,     "pct": round(advance_cr     / (outstanding_cr + advance_cr) * 100, 0) if (outstanding_cr + advance_cr) else 0},
            ],
        },
        "tables": [
            {
                "title": "Top 20 Outstanding Vendors",
                "rows": _rows(top_os),
                "calculated_fields": {
                    "Net Balance (₹)": field(
                        "Total Credit − Total Debit",
                        "Total_Credit − Total_Debit",
                        inputs=[
                            {"field": "Total Debit", "source_file": "General Ledger", "source_record": "Vendor Code"},
                            {"field": "Total Credit", "source_file": "General Ledger", "source_record": "Vendor Code"},
                        ],
                    ),
                },
            },
            {
                "title": "Vendor GL Balance Summary",
                "rows": _rows(full_table.head(500)),
                "calculated_fields": {
                    "Net Balance (₹)": field(
                        "Total Credit − Total Debit",
                        "Total_Credit − Total_Debit",
                        inputs=[
                            {"field": "Total Debit", "source_file": "General Ledger", "source_record": "Vendor Code"},
                            {"field": "Total Credit", "source_file": "General Ledger", "source_record": "Vendor Code"},
                        ],
                    ),
                },
            },
        ],
    }
