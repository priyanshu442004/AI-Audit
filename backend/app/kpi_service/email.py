"""Management report email composition and SMTP delivery."""

from __future__ import annotations

from email.message import EmailMessage
from html import escape
import os
import re
import smtplib
import ssl
from typing import Any


DEFAULT_RECIPIENTS = (
    "anoop@analytx4t.com",
    "amit@analytx4t.com",
)


class EmailConfigurationError(ValueError):
    """Raised when required SMTP settings are incomplete."""


def configured_recipients() -> list[str]:
    raw = os.getenv("KPI_EMAIL_RECIPIENTS")
    values = [item.strip() for item in raw.split(",")] if raw else list(DEFAULT_RECIPIENTS)
    recipients = []
    for value in values:
        if not value:
            continue
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise EmailConfigurationError(f"Invalid address in KPI_EMAIL_RECIPIENTS: {value!r}")
        recipients.append(value)
    if not recipients:
        raise EmailConfigurationError("KPI_EMAIL_RECIPIENTS must contain at least one recipient.")
    return recipients


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
        if not match:
            return None
        value = match.group(0).replace(",", "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _count(value: Any) -> str:
    number = _number(value)
    return "N/A" if number is None else f"{int(number):,}"


def _module_label(module: dict[str, Any]) -> str:
    status_text = {
        "green": "Green – satisfactory",
        "amber": "Amber – needs attention",
        "red": "Red – high priority",
        "review": "Needs review",
    }
    return status_text.get(module["status"], module["rating"])


def _single_line(value: Any) -> str:
    return " ".join(str(value).split())


def build_email(report: dict[str, Any], pdf_content: bytes, recipient: str) -> EmailMessage:
    """Build the required plain-text and HTML messages without sending them."""
    fy = report.get("financial_year") or (report.get("report_period") or {}).get("financial_year")
    if not fy:
        raise ValueError("A reporting financial year is required to build the email.")
    period = report.get("report_period")
    if not period or not period.get("label"):
        raise ValueError("A reporting date range is required to build the email.")
    if fy.startswith("FY "):
        fy_text = fy[3:]
    else:
        fy_text = fy
    subject = f"P2P Audit Analytics – Management Summary Report | {fy}"
    reporting_scope = (
        f"Reporting period: {_single_line(period['label'])}. "
        f"Entity: {_single_line(report.get('source_entity', 'N/A'))}."
    )
    kpis = report["kpis"]
    procurement = report["modules"]["procurement"]
    gate = report["modules"]["gate_entry"]
    stock = report["modules"]["stock_verified"]
    stock_snapshot = report.get("stock_snapshot_date")
    closed_pct = report.get("charts", {}).get("procurement", {}).get("po_value_exposure", {}).get("closed_value_pct")
    if closed_pct is None:
        closed_pct = "N/A"

    stock_exc = None
    pr_exc = _number(kpis["remark_pr_exceptions"]["value"])
    closing_exc = _number(kpis["closing_stock_exceptions"]["value"])
    if pr_exc is not None and closing_exc is not None:
        stock_exc = int(pr_exc + closing_exc)

    procurement_summary = (
        f"Procurement: {_single_line(procurement['name'])} ({_single_line(_module_label(procurement))}); "
        f"{_count(kpis['unique_po_raise']['value'])} POs worth "
        f"{_single_line(kpis['total_po_value']['display_value'])} reviewed, "
        f"{_single_line(closed_pct)}% closed; "
        f"{_count(kpis['cancelled_po_count']['value'])} cancelled and "
        f"{_count(kpis['holiday_exception']['value'])} holiday exceptions; "
        f"{_count(kpis['count_of_excess_price']['value'])} price, "
        f"{_count(kpis['count_of_excess_qty']['value'])} quantity and "
        f"{_count(kpis['count_of_excess_rate']['value'])} rate cases above 5%."
    )
    gate_summary = (
        f"Gate entry: {_single_line(gate['name'])} ({_single_line(_module_label(gate))}); "
        f"{_count(kpis['sequence_exceptions']['value'])} of "
        f"{_count(kpis['total_gate_entry']['value'])} entries dated after goods receipt; "
        f"{_count(kpis['exceeds_3_day_window']['value'])} receipts posted over 3 days later."
    )
    stock_summary = (
        f"Stock: {_single_line(stock['name'])} ({_single_line(_module_label(stock))}); "
        f"{_count(kpis['items_verified']['value'])} items verified, "
        f"{_count(stock_exc)} exceptions."
    )
    if stock_snapshot:
        stock_summary += f" Snapshot as of {_single_line(stock_snapshot)}."

    plain_lines = [
        "Dear Management Team,",
        f"Attached is the P2P Audit Analytics Management Summary for FY {_single_line(fy_text)}. {reporting_scope}",
        procurement_summary,
        gate_summary,
        f"{stock_summary} See the attached report for suggested priorities. Exceptions are review flags, not confirmed errors.",
        "Regards, IKIO Technologies Limited.",
    ]
    plain = "\n".join(plain_lines)
    html_lines = [
        "<p>Dear Management Team,</p>",
        f"<p>Attached is the P2P Audit Analytics Management Summary for FY {escape(_single_line(fy_text))}. {escape(reporting_scope)}</p>",
        f"<p>{escape(procurement_summary)}</p>",
        f"<p>{escape(gate_summary)}</p>",
        f"<p>{escape(stock_summary)} See the attached report for suggested priorities. Exceptions are review flags, not confirmed errors.</p>",
        "<p>Regards, IKIO Technologies Limited.</p>",
    ]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _mail_from()
    message["To"] = recipient
    message.set_content(plain)
    message.add_alternative("\n".join(html_lines), subtype="html")
    filename = f"P2P_Audit_Management_Summary_{report['reporting_date']}.pdf"
    message.add_attachment(pdf_content, maintype="application", subtype="pdf", filename=filename)
    return message


def _mail_from() -> str:
    sender = os.getenv("MAIL_FROM", "").strip()
    if not sender:
        raise EmailConfigurationError("MAIL_FROM must be configured before email delivery.")
    return sender


def send_message(message: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        raise EmailConfigurationError("SMTP_HOST must be configured before email delivery.")
    try:
        port = int(os.getenv("SMTP_PORT", "465"))
    except ValueError as exc:
        raise EmailConfigurationError("SMTP_PORT must be a valid TCP port.") from exc
    username = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "")
    if bool(username) != bool(password):
        raise EmailConfigurationError("SMTP_USER and SMTP_PASS must either both be set or both be blank.")

    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            if username:
                server.login(username, password)
            server.send_message(message)
