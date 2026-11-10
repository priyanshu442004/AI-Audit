"""Deterministic KPI interpretations based on the existing audit rules."""

from __future__ import annotations

from typing import Any

from app.kpi_service.kpi_definitions import KPI_MODULES


_EXCEPTION_KPIS = {
    "cancelled_po_count",
    "holiday_exception",
    "sunday_exception",
    "count_of_excess_qty",
    "count_of_excess_rate",
    "count_of_excess_price",
    "sequence_exceptions",
    "exceeds_3_day_window",
    "remark_pr_exceptions",
    "closing_stock_exceptions",
}

_RED_KPIS = {"sequence_exceptions", "exceeds_3_day_window"}
_PROCUREMENT_CHECKS = (
    "holiday_exception",
    "sunday_exception",
    "count_of_excess_qty",
    "count_of_excess_rate",
    "count_of_excess_price",
)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, str):
            import re

            match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
            if not match:
                return None
            value = match.group(0).replace(",", "")
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, unit: str) -> str:
    number = _number(value)
    if number is None:
        return "not available"
    if unit == "count":
        return f"{int(number):,}"
    if unit == "days":
        return f"{number:g}"
    return str(value)


def _status_for_kpi(kpi: dict[str, Any]) -> str:
    if kpi["value"] is None:
        return "review"
    if kpi["id"] not in _EXCEPTION_KPIS:
        return "informational"
    number = _number(kpi["value"])
    if number is None:
        return "review"
    if number == 0:
        return "green"
    return "red" if kpi["id"] in _RED_KPIS else "amber"


def interpret_report(report: dict[str, Any]) -> dict[str, Any]:
    """Attach reproducible interpretations without changing KPI values or definitions."""
    for kpi in report["kpis"].values():
        kpi["status"] = _status_for_kpi(kpi)
        name = kpi["name"]
        if kpi["value"] is None:
            kpi["interpretation"] = "Source data is unavailable; this KPI cannot be assessed."
            kpi["management_action"] = "Provide and validate the required source data before drawing a conclusion."
        elif kpi["id"] in _EXCEPTION_KPIS:
            amount = _fmt(kpi["value"], kpi["unit"])
            if _number(kpi["value"]) == 0:
                kpi["interpretation"] = f"No {name.lower()} were identified by the existing audit check."
                kpi["management_action"] = "Continue the existing control and retain supporting evidence."
            elif kpi["id"] in _RED_KPIS:
                kpi["interpretation"] = f"{amount} {name.lower()} require verification against the supporting records."
                kpi["management_action"] = "Investigate the affected records and review the gate-entry and GRPO posting sequence."
            else:
                kpi["interpretation"] = f"{amount} {name.lower()} were flagged by the existing audit check and require review."
                kpi["management_action"] = "Review the affected transactions and confirm their supporting approvals and records."
        else:
            kpi["interpretation"] = f"{name} is {kpi['display_value']} for the available reporting period."
            kpi["management_action"] = "Use this measure to monitor activity and reconcile it to the underlying source records."

    for module_id, module_def in KPI_MODULES.items():
        module = report["modules"][module_id]
        module_kpis = [report["kpis"][key] for key in module_def["kpis"]]
        if not module["available"]:
            module["status"] = "review"
            module["rating"] = "Needs review"
            module["summary"] = "Required source data is missing or could not be validated."
            continue

        if any(item["value"] is None for item in module_kpis):
            module["status"] = "review"
            module["rating"] = "Needs review"
            module["summary"] = "One or more required KPI values could not be assessed from the available data."
            continue

        exceptions = [
            item for item in module_kpis
            if item["id"] in _EXCEPTION_KPIS and (_number(item["value"]) or 0) > 0
        ]
        if module_id == "gate_entry" and any(item["id"] in _RED_KPIS for item in exceptions):
            module["status"] = "red"
            module["rating"] = "High priority"
            module["summary"] = f"{_fmt(report['kpis']['sequence_exceptions']['value'], 'count')} sequence exceptions and {_fmt(report['kpis']['exceeds_3_day_window']['value'], 'count')} delayed receipts were identified."
        elif exceptions:
            module["status"] = "amber"
            module["rating"] = "Needs attention"
            module["summary"] = f"{len(exceptions)} exception KPI(s) require management review."
        else:
            module["status"] = "green"
            module["rating"] = "Satisfactory"
            module["summary"] = "No exceptions were identified by the available checks."

    report["management_actions"] = _management_actions(report)
    return report


def _management_actions(report: dict[str, Any]) -> list[dict[str, str]]:
    actions = []

    def add(condition: bool, priority: str, action: str, benefit: str) -> None:
        if condition:
            actions.append({
                "priority": priority,
                "action": action,
                "benefit": benefit,
            })

    kpis = report["kpis"]
    seq = _number(kpis["sequence_exceptions"]["value"])
    delayed = _number(kpis["exceeds_3_day_window"]["value"])
    add(
        seq is not None and seq > 0,
        "HIGH",
        "Investigate the gate-entry records dated after their GRPO posting dates and review the posting sequence control.",
        "Improves chronological control evidence.",
    )
    add(
        delayed is not None and delayed > 0,
        "HIGH",
        "Review GRPOs posted more than three days after gate entry against the approved process.",
        "Reduces delays in receipt recording.",
    )
    po_exceptions = any(
        (_number(kpis[key]["value"]) or 0) > 0
        for key in _PROCUREMENT_CHECKS
        if kpis[key]["value"] is not None
    )
    add(
        po_exceptions,
        "MEDIUM",
        "Review Sunday, holiday, quantity, rate and price exceptions against approvals and supporting records.",
        "Strengthens PO authorization and tolerance controls.",
    )
    stock_exceptions = any(
        (_number(kpis[key]["value"]) or 0) > 0
        for key in ("remark_pr_exceptions", "closing_stock_exceptions")
        if kpis[key]["value"] is not None
    )
    add(
        stock_exceptions,
        "MEDIUM",
        "Reconcile Purchase Register quantities and closing stock mismatches to the Inventory Report.",
        "Improves inventory record accuracy.",
    )
    if not actions:
        actions.append({
            "priority": "LOW",
            "action": "Continue existing controls and retain source evidence for the next reporting period.",
            "benefit": "Maintains a verifiable audit trail.",
        })
    return actions
