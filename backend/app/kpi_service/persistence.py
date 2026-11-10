"""PostgreSQL persistence and cross-instance execution/delivery claims."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db import get_connection, put_connection


def init_management_report_tables() -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kpi_report_executions (
                execution_id VARCHAR(200) PRIMARY KEY,
                job_name VARCHAR(100) NOT NULL,
                scheduled_date DATE,
                timezone VARCHAR(80) NOT NULL,
                reporting_period VARCHAR(200),
                reporting_date DATE,
                started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMPTZ,
                status VARCHAR(32) NOT NULL,
                pdf_filename VARCHAR(255),
                pdf_path TEXT,
                error_details TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_kpi_report_executions_started
                ON kpi_report_executions (started_at DESC);
            CREATE TABLE IF NOT EXISTS kpi_report_email_deliveries (
                id BIGSERIAL PRIMARY KEY,
                execution_id VARCHAR(200) NOT NULL
                    REFERENCES kpi_report_executions(execution_id) ON DELETE CASCADE,
                reporting_date DATE NOT NULL,
                delivery_date DATE,
                recipient VARCHAR(320) NOT NULL,
                subject VARCHAR(500) NOT NULL,
                attachment_filename VARCHAR(255) NOT NULL,
                status VARCHAR(32) NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                sent_at TIMESTAMPTZ,
                failure_reason TEXT
            );
            ALTER TABLE kpi_report_email_deliveries
                ADD COLUMN IF NOT EXISTS delivery_date DATE;
            UPDATE kpi_report_email_deliveries d
            SET delivery_date = COALESCE(
                e.scheduled_date,
                (e.started_at AT TIME ZONE COALESCE(NULLIF(e.timezone, ''), 'Asia/Kolkata'))::date,
                d.reporting_date
            )
            FROM kpi_report_executions e
            WHERE d.execution_id = e.execution_id
              AND d.delivery_date IS NULL;
            ALTER TABLE kpi_report_email_deliveries
                ALTER COLUMN delivery_date SET DEFAULT CURRENT_DATE,
                ALTER COLUMN delivery_date SET NOT NULL;
            ALTER TABLE kpi_report_email_deliveries
                DROP CONSTRAINT IF EXISTS kpi_report_email_deliveries_reporting_date_recipient_key;
            CREATE TABLE IF NOT EXISTS kpi_report_delivery_claims (
                delivery_date DATE NOT NULL,
                recipient VARCHAR(320) NOT NULL,
                execution_id VARCHAR(200) NOT NULL
                    REFERENCES kpi_report_executions(execution_id) ON DELETE CASCADE,
                status VARCHAR(32) NOT NULL,
                PRIMARY KEY (delivery_date, recipient)
            );
            WITH daily_deliveries AS (
                SELECT
                    delivery_date,
                    recipient,
                    (ARRAY_AGG(
                        execution_id
                        ORDER BY CASE WHEN status = 'sent' THEN 0 ELSE 1 END,
                                 sent_at DESC NULLS LAST,
                                 id DESC
                    ))[1] AS execution_id,
                    CASE
                        WHEN BOOL_OR(status = 'sent') THEN 'sent'
                        WHEN BOOL_OR(status = 'sending') THEN 'sending'
                        ELSE 'failed'
                    END AS status
                FROM kpi_report_email_deliveries
                GROUP BY delivery_date, recipient
            )
            INSERT INTO kpi_report_delivery_claims (delivery_date, recipient, execution_id, status)
            SELECT delivery_date, recipient, execution_id, status
            FROM daily_deliveries
            ON CONFLICT (delivery_date, recipient) DO NOTHING;
            CREATE INDEX IF NOT EXISTS idx_kpi_report_email_execution
                ON kpi_report_email_deliveries (execution_id, id);
            """
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        put_connection(conn)


def claim_execution(
    execution_id: str,
    job_name: str,
    scheduled_date: str | None,
    timezone_name: str,
) -> bool:
    """Atomically claim an execution; a unique database row coordinates instances."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO kpi_report_executions
                (execution_id, job_name, scheduled_date, timezone, status)
            VALUES (%s, %s, %s, %s, 'running')
            ON CONFLICT (execution_id) DO NOTHING
            """,
            (execution_id, job_name, scheduled_date, timezone_name),
        )
        inserted = cur.rowcount == 1
        if inserted:
            conn.commit()
            return True

        cur.execute(
            """
            SELECT status, started_at
            FROM kpi_report_executions
            WHERE execution_id = %s
            FOR UPDATE
            """,
            (execution_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.commit()
            return False
        status, started_at = row
        is_stale = status == "running" and (
            started_at is None or (datetime.now(timezone.utc) - started_at).total_seconds() > 1800
        )
        can_retry = status in ("failed", "delivery_failed") or is_stale
        if can_retry:
            cur.execute(
                """
                UPDATE kpi_report_executions
                SET status = 'running', started_at = CURRENT_TIMESTAMP,
                    completed_at = NULL, error_details = NULL
                WHERE execution_id = %s
                """,
                (execution_id,),
            )
        conn.commit()
        return can_retry
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        put_connection(conn)


def update_execution_report(
    execution_id: str,
    *,
    reporting_date: str,
    reporting_period: str,
    pdf_filename: str,
    pdf_path: str,
) -> None:
    _update_execution(
        execution_id,
        """
        UPDATE kpi_report_executions
        SET reporting_date = %s, reporting_period = %s, pdf_filename = %s, pdf_path = %s
        WHERE execution_id = %s
        """,
        (reporting_date, reporting_period, pdf_filename, pdf_path, execution_id),
    )


def finish_execution(execution_id: str, status: str, error_details: str | None = None) -> None:
    if status not in {"completed", "delivery_failed", "failed"}:
        raise ValueError(f"Invalid report execution status: {status}")
    _update_execution(
        execution_id,
        """
        UPDATE kpi_report_executions
        SET status = %s, completed_at = CURRENT_TIMESTAMP, error_details = %s
        WHERE execution_id = %s
        """,
        (status, error_details, execution_id),
    )


def claim_email_delivery(
    execution_id: str,
    reporting_date: str,
    delivery_date: str,
    recipient: str,
    subject: str,
    attachment_filename: str,
) -> bool:
    """Claim a recipient's one daily delivery, allowing failed sends to be retried."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO kpi_report_delivery_claims
                (delivery_date, recipient, execution_id, status)
            VALUES (%s, %s, %s, 'sending')
            ON CONFLICT (delivery_date, recipient) DO NOTHING
            """,
            (delivery_date, recipient, execution_id),
        )
        inserted = cur.rowcount == 1
        if not inserted:
            cur.execute(
                """
                UPDATE kpi_report_delivery_claims
                SET execution_id = %s, status = 'sending'
                WHERE delivery_date = %s AND recipient = %s AND status = 'failed'
                """,
                (execution_id, delivery_date, recipient),
            )
            can_retry = cur.rowcount == 1
            if not can_retry:
                conn.commit()
                return False

        cur.execute(
            """
            INSERT INTO kpi_report_email_deliveries
                (execution_id, reporting_date, delivery_date, recipient, subject, attachment_filename, status, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, 'sending', 1)
            """,
            (execution_id, reporting_date, delivery_date, recipient, subject, attachment_filename),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        put_connection(conn)


def finish_email_delivery(
    execution_id: str,
    delivery_date: str,
    recipient: str,
    status: str,
    failure_reason: str | None = None,
) -> None:
    if status not in {"sent", "failed"}:
        raise ValueError(f"Invalid email delivery status: {status}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE kpi_report_delivery_claims
            SET status = %s
            WHERE delivery_date = %s AND recipient = %s AND execution_id = %s AND status = 'sending'
            """,
            (status, delivery_date, recipient, execution_id),
        )
        if cur.rowcount != 1:
            raise RuntimeError(f"Database update affected no row for email delivery on {delivery_date}.")
        cur.execute(
            """
            UPDATE kpi_report_email_deliveries
            SET status = %s, sent_at = CASE WHEN %s = 'sent' THEN CURRENT_TIMESTAMP ELSE NULL END,
                failure_reason = %s
            WHERE execution_id = %s AND delivery_date = %s AND recipient = %s AND status = 'sending'
            """,
            (status, status, failure_reason, execution_id, delivery_date, recipient),
        )
        if cur.rowcount != 1:
            raise RuntimeError(f"Delivery history update affected no row for {execution_id}.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        put_connection(conn)


def _update_execution(execution_id: str, query: str, params: tuple[Any, ...]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        if execution_id and cur.rowcount != 1:
            raise RuntimeError(f"Database update affected no row for {execution_id}.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        put_connection(conn)


def _release_read_connection(conn: Any, cur: Any) -> None:
    try:
        cur.close()
    finally:
        try:
            conn.rollback()
        finally:
            put_connection(conn)


def get_execution(execution_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT execution_id, job_name, scheduled_date, timezone, reporting_period,
                   reporting_date, started_at, completed_at, status, pdf_filename, error_details
            FROM kpi_report_executions
            WHERE execution_id = %s
            """,
            (execution_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        result = dict(zip([column[0] for column in cur.description], row))
        cur.execute(
            """
            SELECT recipient, subject, attachment_filename, delivery_date,
                   status, attempts, sent_at, failure_reason
            FROM kpi_report_email_deliveries
            WHERE execution_id = %s
            ORDER BY id
            """,
            (execution_id,),
        )
        result["deliveries"] = [
            dict(zip([column[0] for column in cur.description], delivery))
            for delivery in cur.fetchall()
        ]
        return result
    finally:
        _release_read_connection(conn, cur)


def get_execution_history(limit: int = 20) -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT e.execution_id, e.job_name, e.scheduled_date, e.timezone,
                   e.reporting_period, e.reporting_date, e.started_at, e.completed_at,
                   e.status, e.pdf_filename, e.error_details,
                   COALESCE(
                       json_agg(json_build_object(
                          'recipient', d.recipient, 'delivery_date', d.delivery_date,
                          'status', d.status,
                           'sent_at', d.sent_at, 'failure_reason', d.failure_reason
                       )) FILTER (WHERE d.id IS NOT NULL),
                       '[]'::json
                   ) AS deliveries
            FROM kpi_report_executions e
            LEFT JOIN kpi_report_email_deliveries d ON d.execution_id = e.execution_id
            GROUP BY e.execution_id
            ORDER BY e.started_at DESC
            LIMIT %s
            """,
            (max(1, min(int(limit), 100)),),
        )
        return [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]
    finally:
        _release_read_connection(conn, cur)


def get_latest_successful_execution() -> dict[str, Any] | None:
    rows = get_execution_history(100)
    return next((row for row in rows if row["status"] == "completed"), None)


def get_pdf_path(execution_id: str) -> tuple[str, str | None] | None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT pdf_filename, pdf_path FROM kpi_report_executions WHERE execution_id = %s",
            (execution_id,),
        )
        row = cur.fetchone()
        return tuple(row) if row and row[0] else None
    finally:
        _release_read_connection(conn, cur)
