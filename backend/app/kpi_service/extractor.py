"""Map existing dashboard response payloads into the management report contract."""

from __future__ import annotations

from datetime import date
import re
from typing import Any

import pandas as pd

from app.analysis.holiday_utils import parse_p2p_dates
from app.kpi_service.kpi_definitions import KPI_DEFINITIONS, KPI_MODULES


_KPI_SOURCES = {
    "unique_po_raise": ("postatus", "dashboard_kpis", "unique_po_raise"),
    "total_po_value": ("postatus", "dashboard_kpis", "total_po_value"),
    "cancelled_po_count": ("postatus", "dashboard_kpis", "canceled_po_count"),
    "holiday_exception": ("postatus", "dashboard_kpis", "holiday_exception"),
    "sunday_exception": ("postatus", "dashboard_kpis", "sunday_exception"),
    "count_of_excess_qty": ("postatus", "dashboard_kpis", "count_of_excess_qty"),
    "sum_of_excess_qty": ("postatus", "dashboard_kpis", "sum_of_excess_qty"),
    "count_of_excess_rate": ("postatus", "dashboard_kpis", "count_of_excess_rate"),
    "sum_of_excess_rate": ("postatus", "dashboard_kpis", "sum_of_excess_rate"),
    "count_of_excess_price": ("postatus", "dashboard_kpis", "count_of_excess_price"),
    "sum_of_excess_price": ("postatus", "dashboard_kpis", "sum_of_excess_price"),
    "total_gate_entry": ("gateentry", "kpis", "total_gate_entry"),
    "total_value_inr": ("gateentry", "kpis", "total_value_inr"),
    "sequence_exceptions": ("gateentry", "kpis", "sequence_exceptions"),
    "exceeds_3_day_window": ("gateentry", "kpis", "exceeds_3_day_window"),
    "avg_grn_days": ("gateentry", "kpis", "avg_grn_days"),
    "unique_po_numbers": ("gateentry", "kpis", "unique_po_numbers"),
    "unique_grn_nos": ("gateentry", "kpis", "unique_grn_nos"),
    "items_verified": ("stock_verified", "kpis", "total_items"),
    "remark_pr_exceptions": ("stock_verified", "kpis", "pr_exceptions"),
    "closing_stock_exceptions": ("stock_verified", "kpis", "closing_exceptions"),
    "purchase_register_lines": ("stock_verified", "kpis", "pr_lines"),
}


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    return value


def _display_value(value: Any, unit: str, precision: int) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and any(value.endswith(suffix) for suffix in ("Cr", "Lakh")):
        return value
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if unit == "count" or unit in ("items", "lines"):
        return f"{int(numeric):,}"
    if unit == "days":
        return f"{numeric:.{precision}f} days"
    if unit == "INR":
        return f"₹{numeric / 10_000_000:,.{precision}f} Cr"
    if unit.startswith("INR"):
        return f"₹{numeric:,.{precision}f}"
    return f"{numeric:,.{precision}f}"


_REPORTING_DATE_COLUMNS = {
    "purchase_order": (("postingdate", "postdate", "podate"),),
    "gate_entry": (("gateentrydate", "gatedate"),),
    "grpo": (("postingdate", "postdate", "grpodate"),),
    "inventory_report": (("fromdate",), ("todate",)),
    "purchase_register": (("postingdate", "documentdate", "date"),),
}


def _date_values(dfs: dict[str, pd.DataFrame]) -> list[date]:
    values: list[date] = []
    for role, aliases_groups in _REPORTING_DATE_COLUMNS.items():
        frame = dfs.get(role)
        if not isinstance(frame, pd.DataFrame):
            continue
        columns = {
            re.sub(r"[^a-z0-9]", "", str(column).lower()): column
            for column in frame.columns
        }
        for aliases in aliases_groups:
            column = next((columns[alias] for alias in aliases if alias in columns), None)
            if column is None:
                continue
            parsed = parse_p2p_dates(frame[column])
            values.extend(item.date() for item in parsed.dropna())
    return values


def _financial_year_for(value: date) -> str:
    start_year = value.year if value.month >= 4 else value.year - 1
    return f"FY {start_year}-{(start_year + 1) % 100:02d}"


def _report_period(
    dfs: dict[str, pd.DataFrame],
    period_start: date | None = None,
    period_end: date | None = None,
) -> dict[str, str] | None:
    values = _date_values(dfs)
    if period_start is not None:
        values = [value for value in values if value >= period_start]
    if period_end is not None:
        values = [value for value in values if value <= period_end]
    if not values:
        return None
    start, end = min(values), max(values)
    start_fy = _financial_year_for(start)
    end_fy = _financial_year_for(end)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": start.strftime("%d %b %Y") if start == end else f"{start:%d %b %Y} – {end:%d %b %Y}",
        "financial_year": start_fy if start_fy == end_fy else f"{start_fy} to {end_fy}",
    }


def extract_kpis(
    dashboard_results: dict[str, Any],
    stock_results: dict[str, Any],
    dfs: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Copy KPI values and charts from the API payloads consumed by the dashboard."""
    results = {
        "postatus": dashboard_results.get("postatus", {}),
        "gateentry": dashboard_results.get("gateentry", {}),
        "stock_verified": stock_results,
    }
    module_results = {
        "procurement": results["postatus"],
        "gate_entry": results["gateentry"],
        "stock_verified": results["stock_verified"],
    }
    modules: dict[str, dict[str, Any]] = {}
    kpis: dict[str, dict[str, Any]] = {}

    for module_id, definition in KPI_MODULES.items():
        result = module_results[module_id]
        is_available = bool(result) and not result.get("error")
        raw_kpis = result.get("kpis", {}) if is_available else {}
        modules[module_id] = {
            "name": definition["name"],
            "available": is_available,
            "error": result.get("error") if result else None,
            "status": "review" if not is_available else "pending",
        }
        for kpi_id in definition["kpis"]:
            source_result, source_container, source_key = _KPI_SOURCES[kpi_id]
            value = _clean_value(
                results[source_result].get(source_container, {}).get(source_key)
            )
            source_module = {
                "postatus": "procurement",
                "gateentry": "gate_entry",
                "stock_verified": "stock_verified",
            }[source_result]
            if not modules[source_module]["available"]:
                value = None
            kpis[kpi_id] = {
                **KPI_DEFINITIONS[kpi_id],
                "id": kpi_id,
                "value": value,
                "display_value": _display_value(
                    value,
                    KPI_DEFINITIONS[kpi_id]["unit"],
                    KPI_DEFINITIONS[kpi_id]["precision"],
                ),
            }

    return {
        "modules": modules,
        "kpis": kpis,
        "report_period": _report_period(dfs),
        "source_results": module_results,
        "source_entity": "ITL",
        "source_process": "P2P",
    }
