"""End-to-end daily management summary execution."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
from zoneinfo import ZoneInfo

from app.kpi_service.email import (
    build_email,
    configured_recipients,
    send_message,
)
from app.kpi_service.extractor import extract_kpis
from app.kpi_service.interpretation import interpret_report
from app.kpi_service.persistence import (
    claim_email_delivery,
    claim_execution,
    finish_email_delivery,
    finish_execution,
    get_execution,
    update_execution_report,
)
from app.kpi_service.report_pdf import render_management_pdf

logger = logging.getLogger(__name__)


class ReportDataError(ValueError):
    """Raised when source data cannot support a complete management report."""


def report_timezone() -> ZoneInfo:
    name = os.getenv("KPI_SCHEDULE_TIMEZONE", "Asia/Kolkata").strip()
    try:
        return ZoneInfo(name)
    except Exception as exc:
        raise ValueError(f"Invalid KPI_SCHEDULE_TIMEZONE: {name}") from exc


def scheduler_enabled() -> bool:
    return os.getenv("KPI_SCHEDULER_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def scheduler_cron() -> str:
    return os.getenv("KPI_SCHEDULE_CRON", "0 9 * * *").strip()


def admin_token_configured() -> bool:
    return bool(os.getenv("KPI_ADMIN_TOKEN", "").strip())


def _load_dashboard_data() -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    entity = os.getenv("KPI_REPORT_ENTITY", "ITL").strip().upper()
    if entity not in {"ITL", "ISPL"}:
        raise ValueError("KPI_REPORT_ENTITY must be ITL or ISPL.")
    from app.main import get_cached_dfs_or_load, get_result, get_stock_verified_report

    dashboard_results = get_result("combined", entity=entity, process="P2P")
    stock_results = asyncio.run(get_stock_verified_report())
    source_frames = get_cached_dfs_or_load(entity=entity, process="P2P")
    return entity, dashboard_results, stock_results, source_frames


def build_report_data(
    dashboard_results: dict[str, Any],
    stock_results: dict[str, Any],
    source_frames: dict[str, Any],
    entity: str = "ITL",
) -> dict[str, Any]:
    today = datetime.now(report_timezone()).date()
    report = extract_kpis(dashboard_results, stock_results, source_frames)
    report["source_entity"] = entity.upper()
    report = interpret_report(report)

    period = report.get("report_period")
    if not period:
        raise ReportDataError("No reporting dates could be identified in the available source files.")
    report["financial_year"] = period["financial_year"]
    report["reporting_date"] = period["end"]
    report["report_date"] = today.isoformat()

    source_results = report.pop("source_results")
    stock_rows = source_results["stock_verified"].get("rows", [])
    report["stock_snapshot_date"] = stock_rows[0].get("to_date") if stock_rows else None
    report["charts"] = {
        "procurement": source_results["procurement"].get("charts", {}),
        "gate_entry": source_results["gate_entry"].get("charts", {}),
        "stock_verified": {},
    }

    missing_modules = [
        module["name"]
        for module in report["modules"].values()
        if not module["available"]
    ]
    missing_kpis = [kpi["name"] for kpi in report["kpis"].values() if kpi["value"] is None]
    if missing_modules or missing_kpis:
        missing = []
        if missing_modules:
            missing.append("modules: " + ", ".join(missing_modules))
        if missing_kpis:
            missing.append("KPIs: " + ", ".join(missing_kpis))
        raise ReportDataError("Latest source data is incomplete (" + "; ".join(missing) + ").")
    return report


def _pdf_output_dir() -> Path:
    configured = os.getenv("KPI_PDF_OUTPUT_DIR", "").strip()
    return Path(configured) if configured else Path(__file__).resolve().parents[2] / "generated_reports"


def _temporary_dir() -> Path:
    configured = os.getenv("KPI_PDF_TEMP_DIR", "").strip()
    return Path(configured) if configured else Path(tempfile.gettempdir())


def _write_pdf(report: dict[str, Any]) -> tuple[str, str, bytes]:
    filename = f"P2P_Audit_Management_Summary_{report['reporting_date']}.pdf"
    output_dir = _pdf_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = _temporary_dir()
    temp_dir.mkdir(parents=True, exist_ok=True)
    content = render_management_pdf(report)
    with tempfile.TemporaryDirectory(prefix="ikio-kpi-", dir=temp_dir) as temporary:
        staged = Path(temporary) / filename
        staged.write_bytes(content)
        destination = output_dir / filename
        replacement = output_dir / f".{filename}.tmp"
        try:
            shutil.copyfile(staged, replacement)
            os.replace(replacement, destination)
        finally:
            if replacement.exists():
                replacement.unlink()
    return filename, str(destination.resolve()), content


def run_management_report(
    execution_id: str,
    *,
    job_name: str,
    scheduled_date: str | None,
    timezone_name: str,
) -> dict[str, Any] | None:
    """Generate a report and send each recipient at most once per local delivery date."""
    if not claim_execution(execution_id, job_name, scheduled_date, timezone_name):
        return get_execution(execution_id)

    try:
        delivery_date = scheduled_date or datetime.now(ZoneInfo(timezone_name)).date().isoformat()
        entity, dashboard_results, stock_results, source_frames = _load_dashboard_data()
        report = build_report_data(
            dashboard_results,
            stock_results,
            source_frames,
            entity=entity,
        )
        filename, pdf_path, pdf_content = _write_pdf(report)
        period_label = report["report_period"]["label"]
        update_execution_report(
            execution_id,
            reporting_date=report["reporting_date"],
            reporting_period=period_label,
            pdf_filename=filename,
            pdf_path=pdf_path,
        )

        subject = f"P2P Audit Analytics – Management Summary Report | {report['financial_year']}"
        delivery_errors = []
        for recipient in configured_recipients():
            if not claim_email_delivery(
                execution_id,
                report["reporting_date"],
                delivery_date,
                recipient,
                subject,
                filename,
            ):
                continue
            try:
                message = build_email(report, pdf_content, recipient)
                send_message(message)
            except Exception as exc:
                reason = _safe_error(exc)
                finish_email_delivery(execution_id, delivery_date, recipient, "failed", reason)
                delivery_errors.append(f"{recipient}: {reason}")
            else:
                finish_email_delivery(execution_id, delivery_date, recipient, "sent")

        current = get_execution(execution_id)
        unsent = [
            item for item in (current or {}).get("deliveries", [])
            if item.get("status") != "sent"
        ]
        if delivery_errors or unsent:
            finish_execution(
                execution_id,
                "delivery_failed",
                "; ".join(delivery_errors) if delivery_errors else "One or more deliveries remain unresolved.",
            )
        else:
            finish_execution(execution_id, "completed")
    except Exception as exc:
        logger.exception("Daily management report execution failed: %s", execution_id)
        finish_execution(execution_id, "failed", _safe_error(exc))
    return get_execution(execution_id)


def _safe_error(exc: Exception) -> str:
    message = str(exc) or exc.__class__.__name__
    for key in ("SMTP_PASS", "DATABASE_URL", "DEEPSEEK_API_KEY", "KPI_ADMIN_TOKEN"):
        secret = os.getenv(key, "")
        if secret:
            message = message.replace(secret, "[redacted]")
    return message[:2000]
