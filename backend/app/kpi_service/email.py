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


def _percent(numerator: Any, denominator: Any) -> str:
    first, second = _number(numerator), _number(denominator)
    if first is None or second is None or second == 0:
        return "N/A"
    return f"{first / second * 100:.1f}"


def _price_excess_cr(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and value.endswith("Lakh"):
        amount = _number(value)
        return "N/A" if amount is None else f"{amount / 100:.2f}"
    amount = _number(value)
    return "N/A" if amount is None else f"{amount / 10_000_000:.2f}"


def _module_label(module: dict[str, Any]) -> str:
    status_text = {
        "green": "Green – satisfactory",
        "amber": "Amber – needs attention",
        "red": "Red – high priority",
        "review": "Needs review",
    }
    return status_text.get(module["status"], module["rating"])


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
        f"Reporting period: {period['label']}. Entity: {report.get('source_entity', 'N/A')}."
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

    plain_lines = [
        "Dear Management Team,",
        "",
        f"Please find attached the P2P Audit Analytics – Management Summary for FY {fy_text}. It is a 3-page report that explains, in simple terms, how well the Procure-to-Pay (P2P) process is being followed, based on our audit analytics portal.",
        reporting_scope,
        "",
        "Key highlights:",
        "",
        f"1. {procurement['name']} ({_module_label(procurement)})",
        "",
        f"- {_count(kpis['unique_po_raise']['value'])} POs worth {kpis['total_po_value']['display_value']} reviewed; {closed_pct}% of the value is already closed.",
        f"- {_count(kpis['cancelled_po_count']['value'])} cancelled POs and {_count(kpis['holiday_exception']['value'])} holiday exceptions.",
        f"- {_count(kpis['sunday_exception']['value'])} Sunday exceptions flagged; {_count(kpis['count_of_excess_price']['value'])} price, {_count(kpis['count_of_excess_qty']['value'])} quantity and {_count(kpis['count_of_excess_rate']['value'])} rate cases went above the 5% limit (price excess approximately ₹{_price_excess_cr(kpis['sum_of_excess_price']['value'])} Cr).",
        "",
        f"2. {gate['name']} ({_module_label(gate)})",
        "",
        f"- {_count(kpis['sequence_exceptions']['value'])} of {_count(kpis['total_gate_entry']['value'])} gate entries ({_percent(kpis['sequence_exceptions']['value'], kpis['total_gate_entry']['value'])}%) show the gate entry dated after the goods receipt.",
        f"- {_count(kpis['exceeds_3_day_window']['value'])} goods receipts were posted more than 3 days after gate entry; average gate-entry-to-GRN time is {kpis['avg_grn_days']['display_value']}.",
        "",
        f"3. {stock['name']} ({_module_label(stock)})",
        "",
        f"- {_count(kpis['items_verified']['value'])} items verified with {_count(stock_exc)} exceptions in closing stock and purchase register checks.",
        *(
            [f"- Stock verification uses the latest Inventory Report snapshot as of {stock_snapshot}."]
            if stock_snapshot
            else []
        ),
        "",
        "Suggested priorities:",
    ]
    for action in report.get("management_actions", []):
        plain_lines.append(f"- {action['action']}")
    plain_lines.extend([
        "",
        "The full report, with charts and the complete action list, is attached.",
        "",
        "Please note that the exceptions are flags for review and not confirmed errors. I would be happy to walk you through the findings at your convenience.",
        "",
        "Regards,",
        "",
        "IKIO Technologies Limited",
    ])
    plain = "\n".join(plain_lines)
    html_lines = [
        "<p>Dear Management Team,</p>",
        f"<p>Please find attached the P2P Audit Analytics – Management Summary for FY {escape(fy_text)}. It is a 3-page report that explains, in simple terms, how well the Procure-to-Pay (P2P) process is being followed, based on our audit analytics portal.</p>",
        f"<p>{escape(reporting_scope)}</p>",
        "<p><strong>Key highlights:</strong></p>",
        f"<p><strong>1. {escape(procurement['name'])} ({escape(_module_label(procurement))})</strong></p>",
        "<ul>",
        f"<li>{escape(_count(kpis['unique_po_raise']['value']))} POs worth {escape(kpis['total_po_value']['display_value'])} reviewed; {escape(str(closed_pct))}% of the value is already closed.</li>",
        f"<li>{escape(_count(kpis['cancelled_po_count']['value']))} cancelled POs and {escape(_count(kpis['holiday_exception']['value']))} holiday exceptions.</li>",
        f"<li>{escape(_count(kpis['sunday_exception']['value']))} Sunday exceptions flagged; {escape(_count(kpis['count_of_excess_price']['value']))} price, {escape(_count(kpis['count_of_excess_qty']['value']))} quantity and {escape(_count(kpis['count_of_excess_rate']['value']))} rate cases went above the 5% limit (price excess approximately ₹{escape(_price_excess_cr(kpis['sum_of_excess_price']['value']))} Cr).</li>",
        "</ul>",
        f"<p><strong>2. {escape(gate['name'])} ({escape(_module_label(gate))})</strong></p>",
        "<ul>",
        f"<li>{escape(_count(kpis['sequence_exceptions']['value']))} of {escape(_count(kpis['total_gate_entry']['value']))} gate entries ({escape(_percent(kpis['sequence_exceptions']['value'], kpis['total_gate_entry']['value']))}%) show the gate entry dated after the goods receipt.</li>",
        f"<li>{escape(_count(kpis['exceeds_3_day_window']['value']))} goods receipts were posted more than 3 days after gate entry; average gate-entry-to-GRN time is {escape(kpis['avg_grn_days']['display_value'])}.</li>",
        "</ul>",
        f"<p><strong>3. {escape(stock['name'])} ({escape(_module_label(stock))})</strong></p>",
        f"<ul><li>{escape(_count(kpis['items_verified']['value']))} items verified with {escape(_count(stock_exc))} exceptions in closing stock and purchase register checks.</li></ul>",
        *(
            [f"<p>Stock verification uses the latest Inventory Report snapshot as of {escape(stock_snapshot)}.</p>"]
            if stock_snapshot
            else []
        ),
        "<p><strong>Suggested priorities:</strong></p><ul>",
    ]
    html_lines.extend(f"<li>{escape(action['action'])}</li>" for action in report.get("management_actions", []))
    html_lines.extend([
        "</ul>",
        "<p>The full report, with charts and the complete action list, is attached.</p>",
        "<p>Please note that the exceptions are flags for review and not confirmed errors. I would be happy to walk you through the findings at your convenience.</p>",
        "<p>Regards,<br><br>IKIO Technologies Limited</p>",
    ])

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
