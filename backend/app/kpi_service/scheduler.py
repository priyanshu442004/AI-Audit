"""Cron scheduler backed by PostgreSQL execution claims for multi-instance safety."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from threading import Lock
from uuid import uuid4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.db import DB_URL
from app.kpi_service.persistence import get_execution
from app.kpi_service.workflow import (
    report_timezone,
    scheduler_cron,
    scheduler_enabled,
    run_management_report,
)

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None
_scheduler_lock = Lock()


def _run_scheduled_report() -> None:
    zone = report_timezone()
    scheduled_date = datetime.now(zone).date().isoformat()
    execution_id = f"daily-p2p-summary:{scheduled_date}:{zone.key}"
    run_management_report(
        execution_id,
        job_name="daily-p2p-management-summary",
        scheduled_date=scheduled_date,
        timezone_name=zone.key,
    )


def _retry_due_report() -> None:
    """Catch up a missed daily trigger and retry only failed email deliveries."""
    zone = report_timezone()
    now = datetime.now(zone)
    trigger = CronTrigger.from_crontab(scheduler_cron(), timezone=zone)
    last_fire = trigger.get_next_fire_time(None, now - timedelta(days=1))
    if not last_fire or last_fire.date() != now.date() or last_fire > now:
        return
    scheduled_date = last_fire.date().isoformat()
    execution_id = f"daily-p2p-summary:{scheduled_date}:{zone.key}"
    existing = get_execution(execution_id)
    if existing:
        retryable = existing["status"] in {"failed", "delivery_failed"}
        started = existing.get("started_at")
        if existing["status"] == "running" and started is not None:
            retryable = (now - started).total_seconds() > 1800
        if not retryable:
            return
    run_management_report(
        execution_id,
        job_name="daily-p2p-management-summary",
        scheduled_date=scheduled_date,
        timezone_name=zone.key,
    )


def start_scheduler() -> None:
    global _scheduler
    if not scheduler_enabled():
        logger.info("Daily P2P management report scheduler is disabled.")
        return
    with _scheduler_lock:
        if _scheduler and _scheduler.running:
            return
        zone = report_timezone()
        cron = scheduler_cron()
        trigger = CronTrigger.from_crontab(cron, timezone=zone)
        if not DB_URL:
            raise RuntimeError("DATABASE_URL is required for the persistent KPI scheduler.")
        scheduler = BackgroundScheduler(
            timezone=zone,
            jobstores={
                "default": SQLAlchemyJobStore(
                    url=DB_URL,
                    tablename="kpi_management_scheduler_jobs",
                )
            },
        )
        scheduler.add_job(
            _run_scheduled_report,
            trigger=trigger,
            id="daily-p2p-management-summary",
            name="Daily P2P management summary",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=3600,
        )
        scheduler.add_job(
            _retry_due_report,
            trigger=IntervalTrigger(minutes=5, timezone=zone),
            id="daily-p2p-management-summary-retry",
            name="Daily P2P management summary retry",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        scheduler.start()
        _scheduler = scheduler
        logger.info(
            "Daily P2P management report scheduled with cron %s (%s).",
            cron,
            zone.key,
        )


def stop_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
        _scheduler = None


def scheduler_status() -> dict:
    zone = report_timezone()
    cron = scheduler_cron()
    if not scheduler_enabled():
        return {
            "enabled": False,
            "cron": cron,
            "timezone": zone.key,
            "next_run": None,
        }
    if _scheduler and _scheduler.running:
        job = _scheduler.get_job("daily-p2p-management-summary")
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    else:
        next_run = CronTrigger.from_crontab(cron, timezone=zone).get_next_fire_time(
            None,
            datetime.now(zone),
        )
        next_run = next_run.isoformat() if next_run else None
    return {
        "enabled": True,
        "cron": cron,
        "timezone": zone.key,
        "next_run": next_run,
    }


def run_manual_report() -> str:
    zone = report_timezone()
    execution_id = f"manual-p2p-summary:{datetime.now(zone).date().isoformat()}:{uuid4()}"
    return execution_id
