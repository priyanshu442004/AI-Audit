"""Administrator endpoints for scheduler status, execution history, and manual reports."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hmac
import os
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import FileResponse

from app.kpi_service.email import DEFAULT_RECIPIENTS
from app.kpi_service.kpi_definitions import KPI_DEFINITIONS
from app.kpi_service.persistence import (
    get_execution,
    get_execution_history,
    get_latest_successful_execution,
    get_pdf_path,
)
from app.kpi_service.scheduler import run_manual_report, scheduler_status
from app.kpi_service.workflow import (
    admin_token_configured,
    report_timezone,
    run_management_report,
)

router = APIRouter(prefix="/api/management-report", tags=["management-report"])
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="kpi-management-report")


def _require_admin(token: str | None) -> None:
    expected = os.getenv("KPI_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(503, "Manual report administration is disabled until KPI_ADMIN_TOKEN is configured.")
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(401, "Administrator token is invalid.")


@router.get("/status")
def management_report_status(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    latest = get_latest_successful_execution()
    return {
        "scheduler": scheduler_status(),
        "last_successful_run": latest,
        "last_generated_pdf": latest.get("pdf_filename") if latest else None,
        "default_recipients": list(DEFAULT_RECIPIENTS),
    }


@router.get("/definitions")
def management_report_definitions(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    return {"kpis": list(KPI_DEFINITIONS.values())}


@router.get("/history")
def management_report_history(
    limit: int = Query(default=20, ge=1, le=100),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)
    return {"executions": get_execution_history(limit)}


@router.post("/run", status_code=202)
def run_management_report_manually(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    _require_admin(x_admin_token)
    execution_id = run_manual_report()
    zone = report_timezone()
    _executor.submit(
        run_management_report,
        execution_id,
        job_name="manual-p2p-management-summary",
        scheduled_date=None,
        timezone_name=zone.key,
    )
    return {"execution_id": execution_id, "status": "queued"}


@router.get("/executions/{execution_id}")
def management_report_execution(
    execution_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)
    execution = get_execution(execution_id)
    if not execution:
        raise HTTPException(404, "Report execution not found.")
    return execution


@router.get("/executions/{execution_id}/pdf")
def download_management_report_pdf(
    execution_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
):
    _require_admin(x_admin_token)
    saved = get_pdf_path(execution_id)
    if not saved:
        raise HTTPException(404, "No PDF is available for this execution.")
    filename, raw_path = saved
    output_dir = Path(
        os.getenv("KPI_PDF_OUTPUT_DIR", "").strip()
        or Path(__file__).resolve().parents[2] / "generated_reports"
    ).resolve()
    path = Path(raw_path).resolve()
    if path.parent != output_dir or not path.is_file():
        raise HTTPException(404, "The report PDF is unavailable.")
    return FileResponse(path, media_type="application/pdf", filename=filename)
