from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from pypdf import PdfReader

from app.analysis.holiday_utils import load_p2p_holiday_frame, parse_p2p_dates
from app.analysis.po_status import _dashboard_kpis
from app.kpi_service.email import build_email
from app.kpi_service.extractor import extract_kpis, has_dashboard_kpis
from app.kpi_service.kpi_definitions import KPI_DEFINITIONS, KPI_MODULES
from app.kpi_service import persistence
from app.kpi_service.api import _resolve_report_pdf
from app.kpi_service.report_pdf import _fit_line, render_management_pdf
from app.kpi_service.workflow import build_report_data, report_timezone, scheduler_cron


PO_VALUES = {
    "unique_po_raise": 84,
    "total_po_value": "12.34 Cr",
    "canceled_po_count": 0,
    "holiday_exception": 0,
    "sunday_exception": 2,
    "count_of_excess_qty": 3,
    "sum_of_excess_qty": "1.20 Lakh",
    "count_of_excess_rate": 4,
    "sum_of_excess_rate": 123.45,
    "count_of_excess_price": 5,
    "sum_of_excess_price": "6.78 Lakh",
}
GATE_VALUES = {
    "total_gate_entry": 120,
    "total_value_inr": 1_702_900_000,
    "sequence_exceptions": 6,
    "exceeds_3_day_window": 7,
    "avg_grn_days": 2,
    "unique_po_numbers": 48,
    "unique_grn_nos": 115,
}
STOCK_VALUES = {
    "total_items": 90,
    "pr_exceptions": 1,
    "closing_exceptions": 0,
    "pr_lines": 250,
}
DASHBOARD_PO_VALUES = {
    **PO_VALUES,
    "holiday_exception": 9,
    "sum_of_excess_rate": 234.56,
}


def test_scheduler_defaults_to_nine_am_india(monkeypatch):
    monkeypatch.delenv("KPI_SCHEDULE_CRON", raising=False)
    monkeypatch.delenv("KPI_SCHEDULE_TIMEZONE", raising=False)

    assert scheduler_cron() == "0 9 * * *"
    assert report_timezone().key == "Asia/Kolkata"


def test_report_download_resolves_pdf_from_current_output_dir(tmp_path, monkeypatch):
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    filename = "P2P_Audit_Management_Summary_2026-09-30.pdf"
    pdf_path = output_dir / filename
    pdf_path.write_bytes(b"%PDF-1.4 test")

    resolved = _resolve_report_pdf(
        filename,
        str(tmp_path / "previous-deployment" / filename),
        output_dir,
    )

    assert resolved == pdf_path.resolve()


def test_report_download_rejects_paths_outside_report_directories(tmp_path):
    secret_file = tmp_path / "secret.pdf"
    secret_file.write_bytes(b"not a report")

    assert _resolve_report_pdf("../secret.pdf", str(secret_file), tmp_path) is None


def _dashboard_results():
    return {
        "postatus": {
            "kpis": dict(PO_VALUES),
            "dashboard_kpis": dict(DASHBOARD_PO_VALUES),
            "charts": {
                "po_status_distribution": {"total_lines": 100, "open_lines": 10, "closed_lines": 90},
                "po_value_exposure": {
                    "open_value": "1.00 Cr",
                    "closed_value": "11.34 Cr",
                    "closed_value_pct": 91,
                },
            },
        },
        "gateentry": {
            "kpis": dict(GATE_VALUES),
            "charts": {
                "pass_vs_exception": {
                    "total": 120,
                    "integrity_pct": 95,
                    "segments": [
                        {"label": "Pass (Correct Order)", "value": 114},
                        {"label": "Exception (GE > GRPO)", "value": 6},
                    ],
                },
                "detailed_checks": [
                    {"label": "Gate entry after GRPO", "value": 6},
                    {"label": "Exceeds 3 days", "value": 7},
                ],
            },
        },
    }


def _source_frames():
    frames = {
        "purchase_order": pd.DataFrame({"Posting Date": ["2026-10-12"]}),
        "gate_entry": pd.DataFrame({"Gate Entry Date": ["12/10/2026"]}),
        "grpo": pd.DataFrame({"Posting Date": ["2026-10-12"]}),
        "inventory_report": pd.DataFrame({"To Date": ["2026-10-12"]}),
        "purchase_register": pd.DataFrame({"Date": ["2026-10-12"]}),
        "holiday": pd.DataFrame({"Holiday": ["Test Holiday"], "Date": ["2026-10-12"]}),
    }
    frames["holiday"].attrs["covered_years"] = {2026}
    return frames


def _stock_results():
    return {
        "kpis": dict(STOCK_VALUES),
        "rows": [{"to_date": "2026-10-12"}],
    }


def _report_data(frames=None, dashboard=None, stock=None):
    return build_report_data(
        dashboard or _dashboard_results(),
        stock or _stock_results(),
        frames or _source_frames(),
    )


def test_kpi_registry_contains_the_22_fixed_dashboard_definitions():
    assert len(KPI_DEFINITIONS) == 22
    assert sum(len(module["kpis"]) for module in KPI_MODULES.values()) == 22
    assert len({key for module in KPI_MODULES.values() for key in module["kpis"]}) == 22
    assert KPI_DEFINITIONS["sequence_exceptions"]["description"] == (
        "Number of cases where the gate-entry date is later than the corresponding GRPO date, "
        "indicating a chronological sequence anomaly."
    )


def test_extractor_copies_dashboard_response_values_without_recalculating():
    dashboard = _dashboard_results()
    stock = _stock_results()
    extracted = extract_kpis(dashboard, stock, _source_frames())

    assert set(extracted["kpis"]) == set(KPI_DEFINITIONS)
    assert extracted["kpis"]["unique_po_raise"]["value"] == 84
    assert extracted["kpis"]["total_po_value"]["value"] == "12.34 Cr"
    assert extracted["kpis"]["cancelled_po_count"]["value"] == 0
    assert extracted["kpis"]["sum_of_excess_rate"]["value"] == 234.56
    assert extracted["kpis"]["holiday_exception"]["value"] == 9
    assert extracted["kpis"]["items_verified"]["value"] == 90
    assert extracted["kpis"]["purchase_register_lines"]["value"] == 250
    assert extracted["source_results"]["procurement"] is dashboard["postatus"]
    assert extracted["source_results"]["gate_entry"] is dashboard["gateentry"]
    assert extracted["source_results"]["stock_verified"] is stock
    assert extracted["report_period"]["start"] == "2026-10-12"
    assert extracted["report_period"]["end"] == "2026-10-12"


def test_dashboard_cache_contract_rejects_legacy_result_without_dashboard_kpis():
    legacy_result = _dashboard_results()
    legacy_result["postatus"].pop("dashboard_kpis")

    assert not has_dashboard_kpis(legacy_result)
    assert has_dashboard_kpis(_dashboard_results())


def test_dashboard_cache_contract_rejects_partial_dashboard_kpis():
    incomplete_result = _dashboard_results()
    incomplete_result["postatus"]["dashboard_kpis"].pop("sum_of_excess_rate")

    assert not has_dashboard_kpis(incomplete_result)


def test_po_dashboard_kpis_match_the_unfiltered_frontend_cards():
    rows = pd.DataFrame({
        "PO No": ["PO-1", "PO-1", "—"],
        "Line Total": [100, 200, 300],
        "Canceled Status": ["Yes", "Yes", "No"],
        "Holiday & Sunday Exception": ["Holiday - Test", "Sunday", "Regular"],
        "QTY Difference": ["Exception", "Regular", "Exception"],
        "Excess QTY": [1, 2, 3],
        "Rate Difference": ["Exception", "Regular", "Exception"],
        "Excess Rate": [5, 10, 15],
        "Line Total Difference": ["Exception", "Regular", "Exception"],
        "Excess Price": [100_000, 200_000, 300_000],
    })

    assert _dashboard_kpis(rows) == {
        "unique_po_raise": 1,
        "total_po_value": "0.00 Cr",
        "canceled_po_count": 2,
        "holiday_exception": 1,
        "sunday_exception": 1,
        "count_of_excess_qty": 2,
        "sum_of_excess_qty": "0.00 Lakh",
        "count_of_excess_rate": 2,
        "sum_of_excess_rate": 30.0,
        "count_of_excess_price": 2,
        "sum_of_excess_price": "6.00 Lakh",
    }


def test_reporting_period_uses_transaction_dates_not_delivery_or_reference_dates():
    frames = {
        "purchase_order": pd.DataFrame({
            "Posting Date": ["2026-01-02", "2026-09-30"],
            "Document Date": ["2026-01-02", "2026-09-30"],
            "Delivery Date": ["2036-02-27", "2028-04-01"],
        }),
        "gate_entry": pd.DataFrame({
            "Gate Entry Date": ["2026-01-01", "2026-09-30"],
            "GRN Date": ["2020-06-02", "2026-10-01"],
        }),
        "grpo": pd.DataFrame({
            "Posting Date": ["2026-01-01", "2026-09-30"],
            "Delivery Date": ["2026-10-30", "2026-10-30"],
        }),
        "inventory_report": pd.DataFrame({
            "From Date": ["2026-01-01"],
            "To Date": ["2026-09-30"],
        }),
        "holiday": pd.DataFrame({"Date": ["2025-01-01", "2026-12-25"]}),
    }

    period = extract_kpis(_dashboard_results(), _stock_results(), frames)["report_period"]

    assert period["start"] == "2026-01-01"
    assert period["end"] == "2026-09-30"
    assert period["financial_year"] == "FY 2025-26 to FY 2026-27"


def test_report_uses_dashboard_values_without_recomputing_them():
    frames = _source_frames()
    frames["purchase_order"] = pd.DataFrame({
        "Posting Date": ["2025-01-02", "2026-10-12"],
        "Delivery Date": ["2036-02-27", "2026-10-12"],
    })
    results = _dashboard_results()
    report = _report_data(frames=frames, dashboard=results)

    assert report["kpis"]["unique_po_raise"]["value"] == PO_VALUES["unique_po_raise"]
    assert report["report_period"]["start"] == "2025-01-02"
    assert report["report_period"]["end"] == "2026-10-12"
    assert report["financial_year"] == "FY 2024-25 to FY 2026-27"


def test_kpi_card_text_is_fitted_to_its_available_width():
    from reportlab.pdfbase.pdfmetrics import stringWidth

    text, size = _fit_line(
        "A KPI label that is much too long for a compact card",
        width=78,
        font="Helvetica-Bold",
        size=11,
        minimum_size=7.4,
    )

    assert text.endswith("...")
    assert stringWidth(text, "Helvetica-Bold", size) <= 78


def test_missing_dashboard_values_are_not_replaced_with_zero():
    dashboard = _dashboard_results()
    dashboard["postatus"]["dashboard_kpis"].pop("unique_po_raise")
    extracted = extract_kpis(dashboard, {}, _source_frames())

    assert extracted["kpis"]["unique_po_raise"]["value"] is None
    assert extracted["kpis"]["items_verified"]["value"] is None
    assert extracted["kpis"]["remark_pr_exceptions"]["value"] is None
    assert extracted["kpis"]["purchase_register_lines"]["value"] is None
    assert extracted["kpis"]["holiday_exception"]["value"] == 9


def test_interpretation_is_deterministic_and_does_not_change_values():
    report = _report_data()

    assert report["financial_year"] == "FY 2026-27"
    assert report["kpis"]["cancelled_po_count"]["value"] == 0
    assert report["kpis"]["cancelled_po_count"]["status"] == "green"
    assert report["kpis"]["sequence_exceptions"]["status"] == "red"
    assert report["modules"]["gate_entry"]["rating"] == "High priority"
    assert report["modules"]["stock_verified"]["rating"] == "Needs attention"
    assert report["management_actions"]
    assert report["charts"]["procurement"]["po_status_distribution"]["closed_lines"] == 90


def test_pdf_is_exactly_three_pages_and_includes_complete_kpi_descriptions():
    report = _report_data()
    content = render_management_pdf(report)
    reader = PdfReader(BytesIO(content))

    assert len(reader.pages) == 3
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Procurement Transaction Compliance" in text
    assert "GRN & Gate Entry Compliance" in text
    assert "Stock Verified Report" in text
    assert "Vendor Price Comparison Analysis is excluded" in text
    normalized_text = " ".join(text.split())
    for kpi in report["kpis"].values():
        normalized_description = " ".join(kpi["description"].split())
        assert normalized_description in normalized_text


def test_email_is_composed_with_required_subject_bodies_and_single_pdf_attachment(monkeypatch):
    monkeypatch.setenv("MAIL_FROM", "audit@example.test")
    report = _report_data()
    report["stock_snapshot_date"] = "2026-10-12"
    message = build_email(report, b"%PDF safe test attachment", "qa@example.test")

    assert message["Subject"] == "P2P Audit Analytics – Management Summary Report | FY 2026-27"
    assert message["To"] == "qa@example.test"
    plain = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    assert len(plain.splitlines()) == 6
    assert len(html.splitlines()) == 6
    assert "Dear Management Team," in plain
    assert "Reporting period: 12 Oct 2026. Entity: ITL." in plain
    assert "Procurement Transaction Compliance" in plain
    assert "GRN & Gate Entry Compliance" in plain
    assert "Stock Verified Report" in plain
    assert "Snapshot as of 2026-10-12" in plain
    assert "Dear Management Team" in html
    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_content_type() == "application/pdf"
    assert attachments[0].get_filename() == "P2P_Audit_Management_Summary_2026-10-12.pdf"


def test_uploaded_holiday_file_is_combined_with_existing_calendar(tmp_path: Path):
    calendar = tmp_path / "calendar.csv"
    calendar.write_text("Date,Holiday\n2027-01-01,New Year's Day\n", encoding="utf-8")

    frame = load_p2p_holiday_frame(tmp_path)

    assert frame.attrs["source"] == "uploaded"
    assert {2026, 2027}.issubset(frame.attrs["covered_years"])
    assert frame.loc[frame["Date"] == "2027-01-01", "Holiday"].iloc[0] == "New Year's Day"


def test_p2p_date_parser_handles_iso_and_local_dates_in_one_column():
    values = pd.Series(["2026-03-01", "02/03/2026", "2026-03-03"])

    parsed = parse_p2p_dates(values).dt.strftime("%Y-%m-%d").tolist()

    assert parsed == ["2026-03-01", "2026-03-02", "2026-03-03"]


def test_execution_lookup_returns_read_connection_to_pool(monkeypatch):
    class Cursor:
        description = []
        queries = 0

        def execute(self, query, params):
            self.queries += 1
            self.description = (
                [("execution_id",), ("status",)]
                if self.queries == 1
                else [("recipient",), ("delivery_date",), ("status",)]
            )

        def fetchone(self):
            return ("run-1", "completed")

        def fetchall(self):
            return [("qa@example.test", "2026-10-12", "sent")]

        def close(self):
            self.closed = True

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()
            self.rolled_back = False

        def cursor(self):
            return self.cursor_instance

        def rollback(self):
            self.rolled_back = True

    connection = Connection()
    returned = []
    monkeypatch.setattr(persistence, "get_connection", lambda: connection)
    monkeypatch.setattr(persistence, "put_connection", returned.append)

    execution = persistence.get_execution("run-1")

    assert execution == {
        "execution_id": "run-1",
        "status": "completed",
        "deliveries": [{
            "recipient": "qa@example.test",
            "delivery_date": "2026-10-12",
            "status": "sent",
        }],
    }
    assert connection.cursor_instance.closed
    assert connection.rolled_back
    assert returned == [connection]


def test_missing_email_delivery_update_is_reported(monkeypatch):
    class Cursor:
        rowcount = 0

        def execute(self, query, params):
            self.query = query

        def close(self):
            pass

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()
            self.rolled_back = False

        def cursor(self):
            return self.cursor_instance

        def rollback(self):
            self.rolled_back = True

    connection = Connection()
    monkeypatch.setattr(persistence, "get_connection", lambda: connection)
    monkeypatch.setattr(persistence, "put_connection", lambda returned: None)

    with pytest.raises(RuntimeError, match="Database update affected no row"):
        persistence.finish_email_delivery(
            "run-1", "2026-10-12", "qa@example.test", "sent"
        )

    assert connection.rolled_back


def test_daily_email_claim_blocks_a_second_delivery_to_the_same_recipient(monkeypatch):
    class Cursor:
        def __init__(self):
            self.queries = []

        def execute(self, query, params):
            self.queries.append(query)
            self.rowcount = 0 if len(self.queries) <= 2 else 1

        def close(self):
            pass

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()
            self.committed = False

        def cursor(self):
            return self.cursor_instance

        def commit(self):
            self.committed = True

    connection = Connection()
    monkeypatch.setattr(persistence, "get_connection", lambda: connection)
    monkeypatch.setattr(persistence, "put_connection", lambda returned: None)

    claimed = persistence.claim_email_delivery(
        "run-2",
        "2026-09-30",
        "2026-11-03",
        "qa@example.test",
        "Daily report",
        "report.pdf",
    )

    assert not claimed
    assert len(connection.cursor_instance.queries) == 2
    assert connection.committed
