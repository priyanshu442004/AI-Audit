"""
Module D/E — Price Variance & Potential Savings.

D: Per item across vendors, (Max-Min)/Max > 5% = flagged.
E: Savings = (Avg Price - Min Price) × Total Qty per item; rank top items.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from app.cleaning import require_columns, rename_canonical, detect_columns, parse_numeric
from app.config import VARIANCE_TOLERANCE_PCT
from app.analysis.calculated_fields import field, same_row


REQUIRED_GRPO = ["item_code", "grpo_qty", "grpo_rate"]


def run(df_grpo_raw: pd.DataFrame) -> dict:
    grpo_map = require_columns(df_grpo_raw, REQUIRED_GRPO, "GRPO")
    for opt in ["vendor_code", "item_description", "grpo_no"]:
        m2 = detect_columns(df_grpo_raw)
        if opt in m2:
            grpo_map[opt] = m2[opt]

    for opt in ["unit_price"]:
        m2 = detect_columns(df_grpo_raw)
        if opt in m2:
            grpo_map[opt] = m2[opt]
    df = rename_canonical(df_grpo_raw, grpo_map).copy()
    if "grpo_rate" not in df.columns and "unit_price" in df.columns:
        df = df.rename(columns={"unit_price": "grpo_rate"})
    df["grpo_qty"]  = parse_numeric(df["grpo_qty"])
    df["grpo_rate"] = parse_numeric(df["grpo_rate"])
    df = df[df["grpo_rate"].notna() & (df["grpo_rate"] > 0)].copy()
    df = df[df["grpo_qty"].notna()  & (df["grpo_qty"]  > 0)].copy()

    if "item_description" not in df.columns:
        df["item_description"] = df["item_code"]

    # Per item: min, max, avg, total qty
    agg = (
        df.groupby("item_code")
        .agg(
            description=("item_description", "first"),
            min_price=("grpo_rate", "min"),
            max_price=("grpo_rate", "max"),
            avg_price=("grpo_rate", "mean"),
            total_qty=("grpo_qty", "sum"),
            vendor_count=("vendor_code", "nunique") if "vendor_code" in df.columns else ("grpo_qty", "count"),
            total_spend=("grpo_rate", lambda x: (x * df.loc[x.index, "grpo_qty"]).sum()),
        )
        .reset_index()
    )

    # Variance %: (max - min) / max * 100
    agg["price_diff"]    = agg["max_price"] - agg["min_price"]
    agg["variance_pct"]  = np.where(
        agg["max_price"] > 0,
        agg["price_diff"] / agg["max_price"] * 100,
        0.0,
    )
    agg["above_5pct"] = agg["variance_pct"] > VARIANCE_TOLERANCE_PCT

    # Savings: (avg - min) × total_qty
    agg["potential_saving"] = (agg["avg_price"] - agg["min_price"]) * agg["total_qty"]
    agg["potential_saving"] = agg["potential_saving"].clip(lower=0)

    flagged = agg[agg["above_5pct"]].copy()
    total_saving = flagged["potential_saving"].sum()

    items_above_5pct = int(agg["above_5pct"].sum())
    biggest_saving   = float(flagged["potential_saving"].max()) if len(flagged) else 0.0
    rows_reviewed    = len(df)

    top10 = flagged.nlargest(10, "potential_saving")[
        ["item_code", "description", "potential_saving"]
    ].copy()
    top10["rank"] = range(1, len(top10) + 1)
    top10 = top10.rename(columns={
        "item_code": "Item No.", "description": "Description",
        "potential_saving": "Potential Saving (₹)",
    })

    # Full price variance table
    pv_table = flagged.sort_values("potential_saving", ascending=False).head(500)
    pv_table = pv_table.rename(columns={
        "item_code": "Item No.", "description": "Description",
        "min_price": "Lowest Price", "max_price": "Highest Price",
        "price_diff": "Price Diff", "variance_pct": "Variance %",
        "total_qty": "Total Qty", "total_spend": "Total Spend",
        "vendor_count": "Vendor Count", "potential_saving": "Potential Saving (₹)",
    })

    # Potential savings summary
    savings_summary = (
        flagged.nlargest(25, "potential_saving")
        .rename(columns={
            "item_code": "Item No.", "description": "Description",
            "min_price": "Min Price", "avg_price": "Avg Price",
            "total_qty": "Total Qty", "potential_saving": "Potential Saving (₹)",
        })
    )

    def _rows(f):
        return f.fillna("").round(2).astype(str).to_dict(orient="records")

    return {
        "kpis": {
            "items_above_5pct":     items_above_5pct,
            "total_saving_l":       round(total_saving / 1e5, 2),   # in Lakhs
            "total_saving_cr":      round(total_saving / 1e7, 4),
            "biggest_saving":       biggest_saving,
            "rows_reviewed":        rows_reviewed,
        },
        "charts": {
            "top10_savings": _rows(top10),
        },
        "tables": [
            {
                "title": "Price Variance Summary (Items >5%)",
                "rows": _rows(pv_table),
                "calculated_fields": {
                    "Price Diff": field(
                        "Highest Price − Lowest Price",
                        "Max_Price − Min_Price",
                        inputs=[
                            {"field": "Lowest Price", "source_file": "GRPO Report", "source_record": "Item No."},
                            {"field": "Highest Price", "source_file": "GRPO Report", "source_record": "Item No."},
                        ],
                    ),
                    "Variance %": field(
                        "Price Diff ÷ Highest Price × 100",
                        "Price_Diff / Max_Price * 100",
                        inputs=[
                            {"field": "Price Diff", "source_file": "GRPO Report (calculated)", "source_record": "Item No."},
                            {"field": "Highest Price", "source_file": "GRPO Report", "source_record": "Item No."},
                        ],
                    ),
                    "Potential Saving (₹)": field(
                        "(Avg Price − Min Price) × Total Qty",
                        "(Avg_Price − Min_Price) * Total_Qty",
                        inputs=[
                            {"field": "Avg Price", "source_file": "GRPO Report", "source_record": "Item No."},
                            {"field": "Min Price", "source_file": "GRPO Report", "source_record": "Item No."},
                            {"field": "Total Qty", "source_file": "GRPO Report", "source_record": "Item No."},
                        ],
                    ),
                },
            },
            {
                "title": "Potential Savings – Summary Table",
                "rows": _rows(savings_summary),
                "calculated_fields": {
                    "Potential Saving (₹)": field(
                        "(Avg Price − Min Price) × Total Qty",
                        "(Avg_Price − Min_Price) * Total_Qty",
                        inputs=[
                            {"field": "Avg Price", "source_file": "GRPO Report", "source_record": "Item No."},
                            {"field": "Min Price", "source_file": "GRPO Report", "source_record": "Item No."},
                            {"field": "Total Qty", "source_file": "GRPO Report", "source_record": "Item No."},
                        ],
                    ),
                },
            },
        ],
    }
