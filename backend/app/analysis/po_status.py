"""
Module A — Purchase Order Status Analysis.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime

# Helper to find column using case-insensitive aliases
def find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    aliases_set = {a.lower().strip() for a in aliases}
    for col in df.columns:
        if str(col).lower().strip() in aliases_set:
            return col
    return None

def parse_numeric_val(val) -> float:
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except:
        return 0.0

def normalize_id(val) -> str:
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def parse_single_date(val) -> pd.Timestamp | None:
    if pd.isna(val) or val is None or str(val).strip().lower() in ("nan", "none", ""):
        return None
    try:
        from app.cleaning import parse_dates
        s = pd.Series([str(val).strip()])
        parsed = parse_dates(s)
        if not parsed.isna().all():
            return parsed[0]
    except:
        pass
    try:
        return pd.to_datetime(val, errors='coerce', dayfirst=True)
    except:
        return None

# Static list of Indian/corporate public holidays for 2025-2026
STATIC_HOLIDAYS = {
    # 2025
    "2025-01-01", "2025-01-26", "2025-03-14", "2025-03-31", "2025-04-10",
    "2025-04-18", "2025-05-12", "2025-08-15", "2025-10-02", "2025-10-20",
    "2025-10-23", "2025-11-05", "2025-12-25",
    # 2026
    "2026-01-01", "2026-01-26", "2026-03-05", "2026-03-26", "2026-04-02",
    "2026-04-14", "2026-05-01", "2026-08-15", "2026-10-02", "2026-10-18",
    "2026-10-22", "2026-11-09", "2026-12-25"
}

def run(dfs_or_df: dict[str, pd.DataFrame] | pd.DataFrame) -> dict:
    # Support both DataFrame (for tests) and dict of DataFrames (for production)
    if isinstance(dfs_or_df, pd.DataFrame):
        df_po = dfs_or_df
        dfs = {"purchase_order": df_po}
    else:
        dfs = dfs_or_df
        df_po = dfs.get("purchase_order")

    if df_po is None or df_po.empty:
        return {"kpis": {}, "charts": {}, "tables": []}

    df_grpo = dfs.get("grpo")
    # Support both "ap_invoice_report" and "purchase_register"
    df_ap = dfs.get("ap_invoice_report")
    if df_ap is None or df_ap.empty:
        df_ap = dfs.get("purchase_register")
    df_cn = dfs.get("ap_credit_note")
    df_ge = dfs.get("gate_entry")
    df_holiday = dfs.get("holiday")

    # ── 1. Column Detection in PO Sheet ──────────────────────────────────────
    col_po_no = find_col(df_po, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
    col_doc_date = find_col(df_po, ["document date", "doc date", "documentdate"])
    col_post_date = find_col(df_po, ["posting date", "post date", "postingdate", "po date", "po_date"])
    col_doc_status = find_col(df_po, ["document status", "doc status", "documentstatus", "status", "po status"])
    col_currency = find_col(df_po, ["document currency", "currency", "doc currency", "po currency"])
    col_vendor_code = find_col(df_po, ["vendor code", "vendor_code", "card code", "cardcode"])
    col_vendor_name = find_col(df_po, ["vendor name", "vendor_name", "card name", "cardname"])
    col_vendor_group = find_col(df_po, ["vendor group", "vendor_group", "group name", "groupname"])
    col_item_code = find_col(df_po, ["item code", "item_code", "item no", "item no.", "itemno"])
    col_item_desc = find_col(df_po, ["item description", "description", "item_description", "itemname"])
    col_item_group = find_col(df_po, ["item group", "item_group", "group name", "groupname"])
    col_uom = find_col(df_po, ["uom", "unit"])
    col_po_qty = find_col(df_po, ["po qty", "ordered qty", "quantity", "qty", "po_qty"])
    col_po_price = find_col(df_po, ["po price", "unit price", "price", "rate", "po_price"])
    col_doc_rate = find_col(df_po, ["document rate", "doc rate", "rate", "documentrate"])
    col_line_total = find_col(df_po, ["line total", "linetotal", "total", "line_total"])
    col_open_qty = find_col(df_po, ["open qty", "outstanding qty", "openqty", "open_qty"])

    # ── 2. Column Detection in GRPO Sheet ────────────────────────────────────
    col_grpo_po_no = None
    col_grpo_item_code = None
    col_grpo_no = None
    col_grpo_qty = None
    if df_grpo is not None and not df_grpo.empty:
        col_grpo_po_no = find_col(df_grpo, ["po number", "po no", "po no.", "purchase order number", "purchase order no"])
        col_grpo_item_code = find_col(df_grpo, ["item code", "item_code", "item no", "item no.", "itemno"])
        col_grpo_no = find_col(df_grpo, ["grpo no", "grpo no.", "receipt no", "grpo number", "grpono"])
        col_grpo_qty = find_col(df_grpo, ["po qty", "grpo qty", "received qty", "quantity", "qty", "received quantity"])

    # ── 3. Column Detection in AP Sheet ──────────────────────────────────────
    col_ap_po_no = None
    col_ap_grpo_no = None
    col_ap_inv_no = None
    if df_ap is not None and not df_ap.empty:
        col_ap_po_no = find_col(df_ap, ["po number", "po no", "po no.", "purchase order number", "purchase order no"])
        col_ap_grpo_no = find_col(df_ap, ["grpo number", "grpo no", "grpo no.", "grpo_number", "grpo no."])
        col_ap_inv_no = find_col(df_ap, ["ap invoice no", "ap invoice no.", "invoice no", "invoice no.", "ap_invoice_no"])

    # ── 4. Column Detection in Credit Note Sheet ─────────────────────────────
    col_cn_ap_inv_no = None
    col_cn_no = None
    if df_cn is not None and not df_cn.empty:
        col_cn_ap_inv_no = find_col(df_cn, ["ap invoice number", "ap invoice no", "invoice number", "invoice no", "ap_invoice_no"])
        col_cn_no = find_col(df_cn, ["ap credit note no", "ap credit note number", "credit note no", "ap_credit_note_no"])

    # ── 5. Column Detection in Gate Entry Sheet ──────────────────────────────
    col_ge_po_no = None
    col_ge_date = None
    if df_ge is not None and not df_ge.empty:
        col_ge_po_no = find_col(df_ge, ["purchase order number", "purchase order no", "po number", "po no", "po no."])
        col_ge_date = find_col(df_ge, ["gate entry date", "ge date", "date"])

    # ── 6. Pre-aggregate and Build Lookup Dictionaries for O(1) Performance ──
    grpo_lookup = {}
    if df_grpo is not None and not df_grpo.empty and col_grpo_po_no and col_grpo_item_code:
        # Group by PO number and Item Code
        for (po, item), group in df_grpo.groupby([col_grpo_po_no, col_grpo_item_code]):
            po_str = normalize_id(po)
            item_str = normalize_id(item).upper()
            grns = list(group[col_grpo_no].dropna().apply(normalize_id).unique())
            grns = [g for g in grns if g and g.lower() not in ["nan", "none", ""]]
            qty_sum = group[col_grpo_qty].apply(parse_numeric_val).sum()
            grpo_lookup[(po_str, item_str)] = (grns, qty_sum)

    ap_lookup = {}
    if df_ap is not None and not df_ap.empty and col_ap_po_no and col_ap_grpo_no:
        for (po, grpo), group in df_ap.groupby([col_ap_po_no, col_ap_grpo_no]):
            po_str = normalize_id(po)
            grpo_str = normalize_id(grpo)
            invs = list(group[col_ap_inv_no].dropna().apply(normalize_id).unique())
            invs = [i for i in invs if i and i.lower() not in ["nan", "none", ""]]
            ap_lookup[(po_str, grpo_str)] = invs

    cn_lookup = {}
    if df_cn is not None and not df_cn.empty and col_cn_ap_inv_no:
        for inv, group in df_cn.groupby(col_cn_ap_inv_no):
            inv_str = normalize_id(inv)
            cns = list(group[col_cn_no].dropna().apply(normalize_id).unique())
            cns = [c for c in cns if c and c.lower() not in ["nan", "none", ""]]
            cn_lookup[inv_str] = cns

    ge_lookup = {}
    if df_ge is not None and not df_ge.empty and col_ge_po_no:
        for po, group in df_ge.groupby(col_ge_po_no):
            po_str = normalize_id(po)
            dates = list(group[col_ge_date].dropna().astype(str).str.strip().unique())
            dates = [d for d in dates if d and d.lower() not in ["nan", "none", ""]]
            ge_lookup[po_str] = dates

    # Holiday dates parsing
    holiday_dates = set()
    if df_holiday is not None and not df_holiday.empty:
        col_hol_date = find_col(df_holiday, ["date", "holiday date", "holiday", "posting date"])
        if col_hol_date is None:
            col_hol_date = df_holiday.columns[0]
        for val in df_holiday[col_hol_date].dropna():
            try:
                dt = pd.to_datetime(val)
                holiday_dates.add(dt.strftime("%Y-%m-%d"))
            except:
                pass

    # ── 7. Process PO Lines ──────────────────────────────────────────────────
    po_records = df_po.to_dict(orient="records")
    rows = []

    for row in po_records:
        po_num = str(row.get(col_po_no, "")).strip() if col_po_no else ""
        doc_date = str(row.get(col_doc_date, "")).strip() if col_doc_date else ""
        post_date = str(row.get(col_post_date, "")).strip() if col_post_date else ""
        
        # Determine status
        doc_status = ""
        if col_doc_status:
            doc_status = str(row.get(col_doc_status, "")).strip()
        
        # Fallback if doc_status is missing but open_qty is present
        if not doc_status or pd.isna(doc_status) or doc_status == "nan":
            open_qty_val = 0.0
            if col_open_qty:
                open_qty_val = parse_numeric_val(row.get(col_open_qty))
            doc_status = "OPEN" if open_qty_val > 0 else "Closed"

        currency = str(row.get(col_currency, "")).strip() if col_currency else ""
        vendor_code = str(row.get(col_vendor_code, "")).strip() if col_vendor_code else ""
        vendor_name = str(row.get(col_vendor_name, "")).strip() if col_vendor_name else ""
        vendor_country = "India" if currency.upper() == "INR" else "USA"
        vendor_group = str(row.get(col_vendor_group, "")).strip() if col_vendor_group else ""
        item_code = str(row.get(col_item_code, "")).strip() if col_item_code else ""
        item_desc = str(row.get(col_item_desc, "")).strip() if col_item_desc else ""
        item_group = str(row.get(col_item_group, "")).strip() if col_item_group else ""
        uom = str(row.get(col_uom, "")).strip() if col_uom else ""

        ordered_qty = parse_numeric_val(row.get(col_po_qty)) if col_po_qty else 0.0
        po_price = parse_numeric_val(row.get(col_po_price)) if col_po_price else 0.0
        doc_rate = parse_numeric_val(row.get(col_doc_rate)) if col_doc_rate else 1.0
        rate_inr = po_price * doc_rate
        line_val_inr = parse_numeric_val(row.get(col_line_total)) if col_line_total else (ordered_qty * rate_inr)

        # Lookups with normalized IDs
        po_num_norm = normalize_id(po_num)
        item_code_norm = normalize_id(item_code).upper()

        grn_nos, received_qty = grpo_lookup.get((po_num_norm, item_code_norm), ([], 0.0))
        grn_no_str = ", ".join(grn_nos)

        ap_invoices = []
        for g in grn_nos:
            ap_invoices.extend(ap_lookup.get((po_num_norm, g), []))
        ap_invoices = list(set(ap_invoices))
        ap_invoice_no_str = ", ".join(ap_invoices)

        cn_nos = []
        for inv in ap_invoices:
            cn_nos.extend(cn_lookup.get(inv, []))
        cn_nos = list(set(cn_nos))
        cn_no_str = ", ".join(cn_nos)

        pending_qty = ordered_qty - received_qty
        pct_received = (received_qty / ordered_qty * 100.0) if ordered_qty > 0 else 0.0

        # Open Value (INR)
        if doc_status.strip().upper() == "OPEN":
            open_value_inr = pending_qty * rate_inr
        else:
            open_value_inr = "PO is closed"

        # Gate Entry Date
        ge_dates = ge_lookup.get(po_num_norm, [])
        ge_date_str = ", ".join(ge_dates)

        # Days Open
        days_open = 0
        if doc_status.strip().upper() == "OPEN":
            dt_post_parsed = parse_single_date(post_date)
            if dt_post_parsed is not None:
                try:
                    dt_target = pd.to_datetime("2026-03-31")
                    days_open = (dt_target - dt_post_parsed).days
                except:
                    days_open = 0
        else:
            days_open = "PO is closed"

        # %age Variance
        diff = received_qty - ordered_qty
        if diff > 0 and ordered_qty > 0:
            var_pct = (diff / ordered_qty) * 100.0
            variance_str = f"+{var_pct:.2f}%"
        else:
            var_pct = 0.0
            variance_str = "0.00%"

        # Pending Flag
        pending_flag = 1 if received_qty > ordered_qty else 0

        # Open>90d & No receipt
        is_open_90_no_rcpt = 0
        if doc_status.strip().upper() == "OPEN" and isinstance(days_open, (int, float)) and days_open > 90 and received_qty == 0:
            is_open_90_no_rcpt = 1

        # Recv<50%
        recv_lt_50 = 1 if (ordered_qty > 0 and received_qty < ordered_qty * 0.5) else 0

        # Holiday flag (checks if post date or doc date falls on weekend or holiday)
        holiday_flag = 0
        for dt_val in [post_date, doc_date]:
            if not dt_val:
                continue
            dt_parsed = parse_single_date(dt_val)
            if dt_parsed is not None:
                dt_str = dt_parsed.strftime("%Y-%m-%d")
                if dt_str in holiday_dates or dt_str in STATIC_HOLIDAYS or dt_parsed.dayofweek in [5, 6]:
                    holiday_flag = 1
                    break

        rows.append({
            "PO Number": po_num,
            "Document Date": doc_date,
            "Posting Date": post_date,
            "Doc Status": doc_status,
            "Currency": currency,
            "Vendor Code": vendor_code,
            "Vendor Name": vendor_name,
            "Vendor Country": vendor_country,
            "Vendor Group": vendor_group,
            "Item code": item_code,
            "Item Description": item_desc,
            "Item Group": item_group,
            "UOM": uom,
            "GRN No.": grn_no_str,
            "AP Invoice No.": ap_invoice_no_str,
            "AP Credit Note": cn_no_str,
            "Ordered Qty.": ordered_qty,
            "Received Qty.": received_qty,
            "Pending Qty.": pending_qty,
            "%age Received": f"{pct_received:.2f}%",
            "Rate(INR)": rate_inr,
            "Line Value(INR)": line_val_inr,
            "Open Value(INR)": open_value_inr if isinstance(open_value_inr, str) else round(open_value_inr, 2),
            "Gate Entry Date": ge_date_str,
            "Days Open": days_open,
            "%age Variance": variance_str,
            "variance_pct_raw": var_pct, # Helper for frontend coloring
            "Pending Flag": pending_flag,
            "Open>90d & No receipt": is_open_90_no_rcpt,
            "Recv<50%": recv_lt_50,
            "Holiday flag": holiday_flag
        })

    # ── 8. Compute KPIs for Frontend and Tests ───────────────────────────────
    unique_pos = len(set(r["PO Number"] for r in rows if r["PO Number"]))
    po_lines = len(rows)
    open_lines_pending = sum(1 for r in rows if str(r["Doc Status"]).strip().upper() == "OPEN")
    closed_lines = po_lines - open_lines_pending

    po_value_india = sum(r["Line Value(INR)"] for r in rows if r["Vendor Country"] == "India")
    po_value_foreign = sum(r["Line Value(INR)"] for r in rows if r["Vendor Country"] != "India")
    open_po_value = sum(r["Line Value(INR)"] for r in rows if str(r["Doc Status"]).strip().upper() == "OPEN")

    recv_lt_50 = sum(1 for r in rows if r["Recv<50%"] == 1)

    all_grns = set()
    for r in rows:
        if r["GRN No."]:
            for part in r["GRN No."].split(","):
                part_clean = part.strip()
                if part_clean:
                    all_grns.add(part_clean)
    unique_grn_count = len(all_grns)

    all_ap_invs = set()
    for r in rows:
        if r["AP Invoice No."]:
            for part in r["AP Invoice No."].split(","):
                part_clean = part.strip()
                if part_clean:
                    all_ap_invs.add(part_clean)
    unique_ap_count = len(all_ap_invs)

    unique_pos_flagged = sum(1 for r in rows if r["Pending Flag"] == 1)

    # ── 9. Keep Backwards Compatibility for Tests ────────────────────────────
    unique_vendors = len(set(r["Vendor Code"] for r in rows if r["Vendor Code"]))
    total_value_cr = round(sum(r["Line Value(INR)"] for r in rows) / 1e7, 2)
    open_value_cr = round(open_po_value / 1e7, 2)
    pct_open_value = round(open_value_cr / total_value_cr * 100, 1) if total_value_cr else 0.0
    top_vendor_open = 0
    if open_lines_pending > 0:
        vendor_open_counts = {}
        for r in rows:
            if str(r["Doc Status"]).strip().upper() == "OPEN" and r["Vendor Code"]:
                vendor_open_counts[r["Vendor Code"]] = vendor_open_counts.get(r["Vendor Code"], 0) + 1
        if vendor_open_counts:
            top_vendor_open = max(vendor_open_counts.values())

    # Build old PO summary tables to avoid breaking tests
    po_summary_dict = {}
    for r in rows:
        po = r["PO Number"]
        if po not in po_summary_dict:
            po_summary_dict[po] = {
                "PO No": po,
                "Vendor_Code": r["Vendor Code"],
                "Vendor_Name": r["Vendor Name"],
                "Total_Lines": 0,
                "Open_Lines": 0,
                "Total_Qty": 0.0,
                "Open_Qty": 0.0,
                "Total_Value": 0.0,
                "Open_Value": 0.0,
            }
        po_summary_dict[po]["Total_Lines"] += 1
        po_summary_dict[po]["Total_Qty"] += r["Ordered Qty."]
        po_summary_dict[po]["Total_Value"] += r["Line Value(INR)"]
        if str(r["Doc Status"]).strip().upper() == "OPEN":
            po_summary_dict[po]["Open_Lines"] += 1
            po_summary_dict[po]["Open_Qty"] += r["Pending Qty."]
            po_summary_dict[po]["Open_Value"] += r["Line Value(INR)"]

    po_summary = list(po_summary_dict.values())
    for p in po_summary:
        p["Status"] = "Partially Open" if 0 < p["Open_Lines"] < p["Total_Lines"] else ("Open" if p["Open_Lines"] > 0 else "Closed")
    po_summary = sorted(po_summary, key=lambda x: x["Open_Value"], reverse=True)

    vendor_open_dict = {}
    for r in rows:
        if str(r["Doc Status"]).strip().upper() == "OPEN" and r["Vendor Code"]:
            vc = r["Vendor Code"]
            if vc not in vendor_open_dict:
                vendor_open_dict[vc] = {
                    "Vendor Code": vc,
                    "Vendor Name": r["Vendor Name"],
                    "Open_POs": set(),
                    "Open_Lines": 0,
                    "Open_Value": 0.0,
                    "Open_Qty": 0.0,
                }
            vendor_open_dict[vc]["Open_POs"].add(r["PO Number"])
            vendor_open_dict[vc]["Open_Lines"] += 1
            vendor_open_dict[vc]["Open_Value"] += r["Line Value(INR)"]
            vendor_open_dict[vc]["Open_Qty"] += r["Pending Qty."]

    vendor_open = []
    for k, v in vendor_open_dict.items():
        v["Open_POs"] = len(v["Open_POs"])
        vendor_open.append(v)
    vendor_open = sorted(vendor_open, key=lambda x: x["Open_Value"], reverse=True)[:25]

    open_tx = []
    for r in rows:
        if str(r["Doc Status"]).strip().upper() == "OPEN":
            open_tx.append({
                "PO No": r["PO Number"],
                "Vendor Code": r["Vendor Code"],
                "Vendor Name": r["Vendor Name"],
                "Item Code": r["Item code"],
                "Description": r["Item Description"],
                "PO Qty": str(r["Ordered Qty."]),
                "Open Qty": str(r["Pending Qty."]),
                "Unit Price": str(r["Rate(INR)"]),
                "Line Total": str(r["Line Value(INR)"]),
                "PO Date": r["Posting Date"],
            })

    def _to_rows(records_list: list[dict]) -> list[dict]:
        res = []
        for r in records_list:
            res.append({k: str(v) for k, v in r.items()})
        return res

    # Charts segments
    CIRC = 314.0
    open_pct = open_lines_pending / po_lines if po_lines else 0
    closed_pct = 1 - open_pct
    open_dash = round(open_pct * CIRC, 0)
    closed_dash = round(closed_pct * CIRC, 0)

    total_val = po_value_india + po_value_foreign
    closed_val = total_val - open_po_value
    closed_val_pct = round(closed_val / total_val * 100, 0) if total_val else 0.0
    open_val_pct = round(open_po_value / total_val * 100, 0) if total_val else 0.0

    return {
        "kpis": {
            # Old KPIs (kept for unit tests)
            "unique_pos": unique_pos,
            "total_lines": po_lines,
            "open_lines": open_lines_pending,
            "closed_lines": closed_lines,
            "total_value_cr": total_value_cr,
            "open_value_cr": open_value_cr,
            "pct_open_value": pct_open_value,
            "top_vendor_open": top_vendor_open,
            "unique_vendors": unique_vendors,
            # New KPIs (for frontend dashboard)
            "po_lines": po_lines,
            "open_lines_pending": open_lines_pending,
            "po_value_india": po_value_india,
            "po_value_foreign": po_value_foreign,
            "open_po_value": open_po_value,
            "recv_lt_50": recv_lt_50,
            "unique_grn_nos": unique_grn_count,
            "unique_ap_invoices": unique_ap_count,
            "unique_pos_flagged": unique_pos_flagged,
        },
        "charts": {
            "po_status": {
                "total": po_lines,
                "segments": [
                    {"label": "Open", "value": open_lines_pending, "dash": open_dash, "offset": 0},
                    {"label": "Closed", "value": closed_lines, "dash": closed_dash, "offset": -open_dash},
                ],
            },
            "po_value": {
                "closed": {"label": "Closed Value", "value_cr": round(closed_val / 1e7, 2), "pct": closed_val_pct},
                "open": {"label": "Open Value", "value_cr": round(open_po_value / 1e7, 2), "pct": open_val_pct},
            },
        },
        "tables": [
            {"title": "PO Status Summary", "rows": _to_rows(po_summary[:100])},
            {"title": "Top 25 Vendors – Highest Open PO Exposure", "rows": _to_rows(vendor_open)},
            {"title": "Open PO Transaction Data List", "rows": _to_rows(open_tx[:500])},
            {"title": "Purchase Order Line Status Analysis", "rows": rows},
        ],
    }
