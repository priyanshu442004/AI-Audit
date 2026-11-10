"""Fixed-layout, three-page PDF management summary."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import os
from pathlib import Path
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from pypdf import PdfReader

from app.kpi_service.kpi_definitions import KPI_MODULES


_NAVY = colors.HexColor("#101D3A")
_BLUE = colors.HexColor("#2868D7")
_LIGHT_BLUE = colors.HexColor("#EDF4FF")
_PALE = colors.HexColor("#F4F7FB")
_MUTED = colors.HexColor("#64748B")
_GREEN = colors.HexColor("#15966A")
_AMBER = colors.HexColor("#E58A19")
_RED = colors.HexColor("#D7264D")
_BORDER = colors.HexColor("#D9E1EC")
_WHITE = colors.white
_PAGE_W, _PAGE_H = letter
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"


def _register_fonts() -> None:
    global _FONT, _FONT_BOLD
    windows = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
    candidates = [
        (windows / "arial.ttf", windows / "arialbd.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"), Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("IKIO-Regular", str(regular)))
            pdfmetrics.registerFont(TTFont("IKIO-Bold", str(bold)))
            _FONT, _FONT_BOLD = "IKIO-Regular", "IKIO-Bold"
            return


def _safe_text(value: Any) -> str:
    text = "N/A" if value is None else str(value)
    if _FONT == "Helvetica":
        return text.replace("₹", "Rs.").replace("–", "-").replace("’", "'").replace("•", "|")
    return text


def _draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    *,
    font: str = _FONT,
    size: float = 7.3,
    color: colors.Color = _NAVY,
    leading: float | None = None,
    max_lines: int | None = None,
) -> float:
    pdf.setFont(font, size)
    pdf.setFillColor(color)
    lines = simpleSplit(_safe_text(text), font, size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip(" .") + "..."
    line_height = leading or size + 2.2
    for line in lines:
        pdf.drawString(x, y, line)
        y -= line_height
    return y


def _fit_line(text: str, width: float, font: str, size: float, minimum_size: float) -> tuple[str, float]:
    text = _safe_text(text)
    while size > minimum_size and pdfmetrics.stringWidth(text, font, size) > width:
        size = max(minimum_size, size - 0.2)
    if pdfmetrics.stringWidth(text, font, size) <= width:
        return text, size

    ellipsis = "..."
    fitted = text
    while fitted and pdfmetrics.stringWidth(fitted + ellipsis, font, size) > width:
        fitted = fitted[:-1]
    return fitted.rstrip() + ellipsis, size


def _status_color(status: str) -> colors.Color:
    return {
        "green": _GREEN,
        "amber": _AMBER,
        "red": _RED,
        "review": _MUTED,
    }.get(status, _BLUE)


def _draw_header(pdf: canvas.Canvas, report: dict[str, Any]) -> None:
    pdf.setFillColor(_NAVY)
    pdf.rect(0, _PAGE_H - 70, _PAGE_W, 70, fill=1, stroke=0)
    pdf.setFillColor(_BLUE)
    pdf.rect(0, _PAGE_H - 74, _PAGE_W, 4, fill=1, stroke=0)
    pdf.setFillColor(_WHITE)
    pdf.setFont(_FONT_BOLD, 8)
    pdf.drawString(34, _PAGE_H - 21, "IKIO  |  TECHNOLOGIES LIMITED")
    pdf.setFont(_FONT, 6.4)
    pdf.drawString(34, _PAGE_H - 33, "PROCUREMENT AUDIT SUITE  |  P2P AUDIT ANALYTICS")
    pdf.setFont(_FONT_BOLD, 14)
    pdf.drawString(34, _PAGE_H - 53, "P2P Audit - Management Summary")
    period = report.get("report_period") or {}
    period_text = period.get("label") or "Reporting period unavailable"
    fy = report.get("financial_year") or period.get("financial_year") or "Financial year unavailable"
    pdf.setFont(_FONT, 6.6)
    pdf.drawRightString(_PAGE_W - 32, _PAGE_H - 22, fy)
    pdf.drawRightString(_PAGE_W - 32, _PAGE_H - 34, f"Audit period: {period_text}")
    pdf.drawRightString(_PAGE_W - 32, _PAGE_H - 47, f"Report date: {report.get('report_date', 'N/A')}  |  Confidential")


def _draw_footer(pdf: canvas.Canvas, page: int, report: dict[str, Any]) -> None:
    period = report.get("financial_year") or (report.get("report_period") or {}).get("financial_year") or ""
    pdf.setStrokeColor(_BORDER)
    pdf.setLineWidth(0.5)
    pdf.line(32, 34, _PAGE_W - 32, 34)
    pdf.setFillColor(_MUTED)
    pdf.setFont(_FONT, 6.2)
    pdf.drawString(32, 22, f"Confidential - for management use only. Based on available P2P source data, {period}.")
    pdf.drawRightString(_PAGE_W - 32, 22, f"Page {page} of 3")


def _draw_heading(pdf: canvas.Canvas, x: float, y: float, title: str, *, size: float = 11) -> None:
    pdf.setFillColor(_NAVY)
    pdf.setFont(_FONT_BOLD, size)
    pdf.drawString(x, y, title)


def _draw_status_badge(pdf: canvas.Canvas, x: float, y: float, label: str, status: str, width: float = 104) -> None:
    color = _status_color(status)
    pdf.setFillColor(color)
    pdf.roundRect(x, y - 4, width, 16, 3, fill=1, stroke=0)
    pdf.setFillColor(_WHITE)
    pdf.setFont(_FONT_BOLD, 6.4)
    pdf.drawCentredString(x + width / 2, y + 1, _safe_text(label.upper()))


def _draw_kpi_card(pdf: canvas.Canvas, x: float, y: float, width: float, height: float, kpi: dict[str, Any]) -> None:
    status = kpi.get("status", "review")
    pdf.setFillColor(_WHITE)
    pdf.setStrokeColor(_status_color(status) if status != "informational" else _BLUE)
    pdf.setLineWidth(1)
    pdf.roundRect(x, y - height, width, height, 4, fill=1, stroke=1)
    pdf.setFillColor(_MUTED)
    name, name_size = _fit_line(kpi["name"].upper(), width - 14, _FONT_BOLD, 5.7, 4.2)
    pdf.setFont(_FONT_BOLD, name_size)
    pdf.drawString(x + 7, y - 10, name)
    value = kpi.get("display_value", "N/A")
    pdf.setFillColor(_status_color(status) if status in {"red", "amber"} else _NAVY if status != "review" else _MUTED)
    value, value_size = _fit_line(value, width - 14, _FONT_BOLD, 11, 7.4)
    pdf.setFont(_FONT_BOLD, value_size)
    pdf.drawString(x + 7, y - 23, value)
    _draw_wrapped(
        pdf,
        kpi.get("description", ""),
        x + 7,
        y - 32,
        width - 14,
        size=4.7,
        color=_MUTED,
        leading=5.5,
    )


def _draw_kpi_grid(
    pdf: canvas.Canvas,
    report: dict[str, Any],
    module: str,
    x: float,
    top: float,
    cols: int,
    card_h: float,
    gap_x: float = 6,
    gap_y: float = 6,
) -> float:
    keys = KPI_MODULES[module]["kpis"]
    card_w = (_PAGE_W - 2 * x - (cols - 1) * gap_x) / cols
    row_heights = []
    for index, key in enumerate(keys):
        row, _ = divmod(index, cols)
        if row == len(row_heights):
            row_keys = keys[index:index + cols]
            max_lines = max(
                len(simpleSplit(
                    _safe_text(report["kpis"][row_key].get("description", "")),
                    _FONT,
                    4.7,
                    card_w - 14,
                ))
                for row_key in row_keys
            )
            row_heights.append(max(card_h, 42 + (max_lines - 1) * 5.5))
    row_tops = [top]
    for row_height in row_heights[:-1]:
        row_tops.append(row_tops[-1] - row_height - gap_y)
    for index, key in enumerate(keys):
        row, col = divmod(index, cols)
        cx = x + col * (card_w + gap_x)
        cy = row_tops[row]
        _draw_kpi_card(pdf, cx, cy, card_w, row_heights[row], report["kpis"][key])
    return row_tops[-1] - row_heights[-1]


def _draw_overview_table(pdf: canvas.Canvas, report: dict[str, Any], x: float, top: float) -> float:
    widths = [138, 225, 94, 91]
    headers = ["AREA REVIEWED", "WHAT IT CHECKS", "KEY RESULT", "RATING"]
    height = 20
    pdf.setFillColor(_NAVY)
    pdf.rect(x, top - height, sum(widths), height, fill=1, stroke=0)
    cursor = x
    for header, width in zip(headers, widths):
        pdf.setFillColor(_WHITE)
        pdf.setFont(_FONT_BOLD, 5.8)
        pdf.drawString(cursor + 5, top - 13, header)
        cursor += width
    rows = [
        ("procurement", "Checks PO working-day, quantity, rate and price rules."),
        ("gate_entry", "Checks gate-entry and goods-receipt sequence and timing."),
        ("stock_verified", "Checks Purchase Register and calculated stock balances."),
    ]
    y = top - height
    for index, (module_id, what) in enumerate(rows):
        row_h = 24
        fill = _WHITE if index % 2 == 0 else _PALE
        pdf.setFillColor(fill)
        pdf.rect(x, y - row_h, sum(widths), row_h, fill=1, stroke=0)
        module = report["modules"][module_id]
        result = module["summary"]
        row_values = [module["name"], what, result, module["rating"]]
        cursor = x
        for col, (value, width) in enumerate(zip(row_values, widths)):
            pdf.setFillColor(_NAVY)
            _draw_wrapped(
                pdf,
                value,
                cursor + 5,
                y - 9,
                width - 10,
                font=_FONT_BOLD if col in (0, 3) else _FONT,
                size=5.4,
                color=_status_color(module["status"]) if col == 3 else _NAVY,
                leading=6.4,
                max_lines=3,
            )
            cursor += width
        pdf.setStrokeColor(_BORDER)
        pdf.line(x, y - row_h, x + sum(widths), y - row_h)
        y -= row_h
    return y


def _draw_donut(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    radius: float,
    values: list[tuple[str, float, colors.Color]],
    center_label: str,
) -> None:
    total = sum(max(0, value) for _, value, _ in values)
    if total <= 0:
        pdf.setStrokeColor(_BORDER)
        pdf.setLineWidth(10)
        pdf.circle(x, y, radius, stroke=1, fill=0)
        pdf.setFillColor(_MUTED)
        pdf.setFont(_FONT, 6.4)
        pdf.drawCentredString(x, y - 2, "No data")
        return
    angle = 90
    for _, value, color in values:
        if value <= 0:
            continue
        extent = value / total * 360
        pdf.setFillColor(color)
        pdf.wedge(x - radius, y - radius, x + radius, y + radius, angle, extent, fill=1, stroke=0)
        angle += extent
    pdf.setFillColor(_WHITE)
    pdf.circle(x, y, radius * 0.58, stroke=0, fill=1)
    pdf.setFillColor(_NAVY)
    pdf.setFont(_FONT_BOLD, 9)
    pdf.drawCentredString(x, y + 1, center_label)
    pdf.setFillColor(_MUTED)
    pdf.setFont(_FONT, 5.8)
    pdf.drawCentredString(x, y - 9, "reviewed")


def _draw_legend(pdf: canvas.Canvas, x: float, y: float, values: list[tuple[str, float, colors.Color]]) -> None:
    for label, amount, color in values:
        pdf.setFillColor(color)
        pdf.circle(x, y + 2, 3, fill=1, stroke=0)
        pdf.setFillColor(_NAVY)
        pdf.setFont(_FONT, 6)
        pdf.drawString(x + 8, y, f"{label}: {_safe_text(f'{amount:,.0f}')}")
        y -= 13


def _draw_bar_chart(
    pdf: canvas.Canvas,
    x: float,
    top: float,
    width: float,
    rows: list[tuple[str, float | None, colors.Color]],
    *,
    row_h: float = 17,
) -> None:
    available = [value for _, value, _ in rows if value is not None]
    max_value = max(available, default=0)
    label_w = width * 0.42
    value_w = 34
    bar_w = width - label_w - value_w - 8
    y = top
    if not rows or not available:
        pdf.setFillColor(_MUTED)
        pdf.setFont(_FONT, 7)
        pdf.drawString(x, y - 12, "No validated chart data available.")
        return
    for label, value, color in rows:
        _draw_wrapped(pdf, label, x, y - 7, label_w - 4, size=5.7, color=_NAVY, leading=6.2, max_lines=2)
        bx = x + label_w
        pdf.setFillColor(_PALE)
        pdf.roundRect(bx, y - 10, bar_w, 8, 2, fill=1, stroke=0)
        if value is not None and max_value > 0:
            pdf.setFillColor(color)
            pdf.roundRect(bx, y - 10, max(2, bar_w * value / max_value), 8, 2, fill=1, stroke=0)
            shown = f"{value:,.0f}"
        else:
            shown = "N/A"
        pdf.setFillColor(_NAVY)
        pdf.setFont(_FONT_BOLD, 5.8)
        pdf.drawRightString(x + width, y - 8, shown)
        y -= row_h


def _draw_what_this_means(pdf: canvas.Canvas, report: dict[str, Any], module: str, x: float, y: float, width: float) -> None:
    module_info = report["modules"][module]
    pdf.setFillColor(_LIGHT_BLUE)
    pdf.roundRect(x, y - 48, width, 48, 4, fill=1, stroke=0)
    pdf.setFillColor(_BLUE)
    pdf.rect(x, y - 48, 3, 48, fill=1, stroke=0)
    pdf.setFillColor(_BLUE)
    pdf.setFont(_FONT_BOLD, 7)
    pdf.drawString(x + 10, y - 12, "WHAT THIS MEANS")
    _draw_wrapped(pdf, module_info["summary"], x + 10, y - 24, width - 20, size=6.2, color=_NAVY, leading=7.1, max_lines=3)


def _fmt_currency(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str) and value.endswith(("Cr", "Lakh")):
        return value
    try:
        return f"₹{float(value) / 10_000_000:,.2f} Cr"
    except (TypeError, ValueError):
        return str(value)


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


def render_management_pdf(report: dict[str, Any]) -> bytes:
    """Render a fixed three-page PDF and verify its physical page count."""
    _register_fonts()
    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=letter, pageCompression=1)
    pdf.setTitle("P2P Audit - Management Summary")
    pdf.setAuthor("IKIO Technologies Limited")

    _draw_page_one(pdf, report)
    _draw_page_two(pdf, report)
    _draw_page_three(pdf, report)
    pdf.save()

    content = stream.getvalue()
    page_count = len(PdfReader(BytesIO(content)).pages)
    if page_count != 3:
        raise ValueError(f"Management report PDF must contain exactly 3 pages; generated {page_count}.")
    return content


def _draw_page_one(pdf: canvas.Canvas, report: dict[str, Any]) -> None:
    _draw_header(pdf, report)
    _draw_heading(pdf, 32, 700, "EXECUTIVE SUMMARY", size=7.2)
    modules = report["modules"]
    summary = (
        f"This report summarizes the available P2P audit checks for {report.get('report_period', {}).get('label', 'the reporting period')}. "
        f"Procurement is {modules['procurement']['rating'].lower()}, gate-entry controls are {modules['gate_entry']['rating'].lower()}, "
        f"and stock verification is {modules['stock_verified']['rating'].lower()}. "
        "All figures are sourced from the existing dashboard calculations; missing source values are shown as N/A."
    )
    _draw_wrapped(pdf, summary, 32, 687, _PAGE_W - 64, size=7.0, leading=9.0, max_lines=3)

    table_bottom = _draw_overview_table(pdf, report, 32, 656)
    _draw_heading(pdf, 32, table_bottom - 19, "1  Procurement Transaction Compliance Review")
    _draw_status_badge(pdf, _PAGE_W - 146, table_bottom - 23, modules["procurement"]["rating"], modules["procurement"]["status"])
    _draw_wrapped(
        pdf,
        "Checks that purchase orders were raised on working days and within the existing quantity, rate and price rules.",
        32,
        table_bottom - 32,
        _PAGE_W - 64,
        size=6.4,
        color=_MUTED,
    )
    grid_bottom = _draw_kpi_grid(pdf, report, "procurement", 32, table_bottom - 45, 4, 38)

    chart_y = grid_bottom - 28
    pdf.setFillColor(_PALE)
    pdf.roundRect(32, chart_y - 125, 265, 120, 4, fill=1, stroke=0)
    pdf.roundRect(307, chart_y - 125, _PAGE_W - 339, 120, 4, fill=1, stroke=0)
    _draw_heading(pdf, 42, chart_y - 19, "PO line status: Open vs Closed", size=7.2)
    po_charts = report.get("charts", {}).get("procurement", {})
    status = po_charts.get("po_status_distribution", {})
    closed = status.get("closed_lines")
    opened = status.get("open_lines")
    _draw_donut(
        pdf,
        99,
        chart_y - 77,
        30,
        [("Closed", float(closed) if closed is not None else 0, _GREEN), ("Open", float(opened) if opened is not None else 0, _AMBER)],
        f"{int(status['total_lines']):,}" if status.get("total_lines") is not None else "N/A",
    )
    _draw_legend(pdf, 147, chart_y - 59, [("Closed", float(closed) if closed is not None else 0, _GREEN), ("Open", float(opened) if opened is not None else 0, _AMBER)])

    _draw_heading(pdf, 317, chart_y - 19, "PO value exposure (₹ Crore)", size=7.2)
    exposure = po_charts.get("po_value_exposure", {})
    value_rows = [
        ("Closed value", _number(exposure.get("closed_value")), _GREEN),
        ("Open value", _number(exposure.get("open_value")), _AMBER),
    ]
    _draw_bar_chart(pdf, 317, chart_y - 45, _PAGE_W - 350, value_rows, row_h=26)
    _draw_wrapped(pdf, "Open value represents money not yet paid out and material still to be delivered.", 317, chart_y - 106, _PAGE_W - 350, size=5.4, color=_MUTED, max_lines=2)

    _draw_what_this_means(pdf, report, "procurement", 32, chart_y - 140, _PAGE_W - 64)
    _draw_footer(pdf, 1, report)
    pdf.showPage()


def _draw_page_two(pdf: canvas.Canvas, report: dict[str, Any]) -> None:
    _draw_header(pdf, report)
    modules = report["modules"]
    _draw_heading(pdf, 32, 700, "2  GRN & Gate Entry Compliance Review")
    _draw_status_badge(pdf, _PAGE_W - 146, 696, modules["gate_entry"]["rating"], modules["gate_entry"]["status"])
    _draw_wrapped(
        pdf,
        "Checks whether the paperwork follows the required order: vendor bill, gate entry, goods receipt (GRN), and AP invoice.",
        32,
        684,
        _PAGE_W - 64,
        size=6.3,
        color=_MUTED,
        max_lines=2,
    )
    gate_bottom = _draw_kpi_grid(pdf, report, "gate_entry", 32, 658, 4, 40)
    chart_top = gate_bottom - 22
    pdf.setFillColor(_PALE)
    pdf.roundRect(32, chart_top - 126, 222, 121, 4, fill=1, stroke=0)
    pdf.roundRect(264, chart_top - 126, _PAGE_W - 296, 121, 4, fill=1, stroke=0)
    _draw_heading(pdf, 42, chart_top - 18, "Audit pass vs exception", size=7.2)
    gate = report.get("charts", {}).get("gate_entry", {})
    pass_chart = gate.get("pass_vs_exception", {})
    segments = pass_chart.get("segments", [])
    values = [
        (
            "In order" if "pass" in segment["label"].lower() else "Out of order",
            float(segment["value"]),
            _GREEN if "pass" in segment["label"].lower() else _RED,
        )
        for segment in segments
    ]
    pass_pct = (
        f"{pass_chart['integrity_pct']:.1f}%"
        if pass_chart.get("integrity_pct") is not None
        else "N/A"
    )
    _draw_donut(pdf, 98, chart_top - 77, 31, values, pass_pct)
    _draw_legend(pdf, 146, chart_top - 65, values)

    _draw_heading(pdf, 274, chart_top - 18, "Chronological control checks", size=7.2)
    detailed = gate.get("detailed_checks", [])
    chart_rows = [
        (row["label"], _number(row.get("value")), _RED if "exception" in row["label"].lower() or "exceeds" in row["label"].lower() else _BLUE)
        for row in detailed[:5]
    ]
    _draw_bar_chart(pdf, 274, chart_top - 38, _PAGE_W - 306, chart_rows, row_h=15)
    _draw_what_this_means(pdf, report, "gate_entry", 32, chart_top - 141, _PAGE_W - 64)

    stock_top = chart_top - 207
    _draw_heading(pdf, 32, stock_top, "3  Stock Verified Report")
    _draw_status_badge(pdf, _PAGE_W - 146, stock_top - 4, modules["stock_verified"]["rating"], modules["stock_verified"]["status"])
    _draw_wrapped(
        pdf,
        "Recalculates closing stock by item and checks Purchase Register quantities against stock received through GRPO.",
        32,
        stock_top - 15,
        _PAGE_W - 64,
        size=6.3,
        color=_MUTED,
    )
    stock_bottom = _draw_kpi_grid(pdf, report, "stock_verified", 32, stock_top - 28, 4, 40)
    _draw_what_this_means(pdf, report, "stock_verified", 32, stock_bottom - 12, _PAGE_W - 64)
    _draw_footer(pdf, 2, report)
    pdf.showPage()


def _draw_page_three(pdf: canvas.Canvas, report: dict[str, Any]) -> None:
    _draw_header(pdf, report)
    _draw_heading(pdf, 32, 700, "OVERALL PICTURE", size=7.2)
    _draw_heading(pdf, 32, 684, "Where the exceptions sit", size=11)
    _draw_wrapped(
        pdf,
        "Exception counts are shown by audit check; PO-level and gate-entry-level counts are not directly additive.",
        32,
        669,
        _PAGE_W - 64,
        size=6.4,
        color=_MUTED,
    )
    keys = [
        ("sequence_exceptions", _RED),
        ("exceeds_3_day_window", _RED),
        ("sunday_exception", _AMBER),
        ("count_of_excess_price", _BLUE),
        ("count_of_excess_qty", _BLUE),
        ("count_of_excess_rate", _BLUE),
        ("holiday_exception", _AMBER),
        ("cancelled_po_count", _MUTED),
        ("remark_pr_exceptions", _GREEN),
        ("closing_stock_exceptions", _GREEN),
    ]
    rows = [
        (report["kpis"][key]["name"], _number(report["kpis"][key]["value"]), color)
        for key, color in keys
    ]
    _draw_bar_chart(pdf, 72, 640, _PAGE_W - 105, rows, row_h=14)

    actions_top = 486
    _draw_heading(pdf, 32, actions_top, "RECOMMENDED ACTIONS", size=7.2)
    _draw_heading(pdf, 32, actions_top - 15, "What management should do next", size=11)
    y = actions_top - 28
    columns = [43, 290, 183]
    headers = ["PRIORITY", "ACTION", "EXPECTED BENEFIT"]
    header_h = 19
    pdf.setFillColor(_NAVY)
    pdf.rect(32, y - header_h, sum(columns), header_h, fill=1, stroke=0)
    cursor = 32
    for header, width in zip(headers, columns):
        pdf.setFillColor(_WHITE)
        pdf.setFont(_FONT_BOLD, 5.8)
        pdf.drawString(cursor + 5, y - 12, header)
        cursor += width
    y -= header_h
    for index, action in enumerate(report.get("management_actions", [])):
        row_h = 40
        pdf.setFillColor(_WHITE if index % 2 == 0 else _PALE)
        pdf.rect(32, y - row_h, sum(columns), row_h, fill=1, stroke=0)
        priority_color = _RED if action["priority"] == "HIGH" else _AMBER if action["priority"] == "MEDIUM" else _MUTED
        pdf.setFillColor(priority_color)
        pdf.rect(32, y - row_h, columns[0], row_h, fill=1, stroke=0)
        pdf.setFillColor(_WHITE)
        pdf.setFont(_FONT_BOLD, 6.2)
        pdf.drawCentredString(32 + columns[0] / 2, y - 22, action["priority"])
        _draw_wrapped(pdf, action["action"], 32 + columns[0] + 6, y - 10, columns[1] - 12, size=6, leading=7.2, max_lines=4)
        _draw_wrapped(pdf, action["benefit"], 32 + columns[0] + columns[1] + 6, y - 10, columns[2] - 12, size=6, color=_MUTED, leading=7.2, max_lines=4)
        pdf.setStrokeColor(_BORDER)
        pdf.line(32, y - row_h, _PAGE_W - 32, y - row_h)
        y -= row_h

    scope_y = max(76, y - 14)
    pdf.setFillColor(_PALE)
    pdf.roundRect(32, scope_y - 54, _PAGE_W - 64, 54, 4, fill=1, stroke=0)
    pdf.setFillColor(_NAVY)
    pdf.setFont(_FONT_BOLD, 6.3)
    pdf.drawString(42, scope_y - 13, "SCOPE AND READING NOTES")
    scope = (
        "This summary covers Procurement Transaction Compliance, GRN & Gate Entry Compliance and Stock Verified Report. "
        "Vendor Price Comparison Analysis is excluded. KPI values are copied from the dashboard API responses; blank or "
        "unavailable source data is not treated as zero. Exceptions are review flags and are not confirmed errors. "
        "No targets or historical trends are inferred when source values are unavailable."
    )
    _draw_wrapped(pdf, scope, 42, scope_y - 26, _PAGE_W - 84, size=5.9, color=_MUTED, leading=7, max_lines=4)
    _draw_footer(pdf, 3, report)
    pdf.showPage()


def save_management_pdf(report: dict[str, Any], output_dir: str | Path, reporting_date: str) -> tuple[str, bytes]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    content = render_management_pdf(report)
    filename = f"P2P_Audit_Management_Summary_{reporting_date}.pdf"
    output_path = directory / filename
    temporary_path = output_path.with_suffix(".pdf.tmp")
    try:
        temporary_path.write_bytes(content)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return str(output_path), content
