"""
Module A — Purchase Order Status Analysis (ITL & General P2P Pipeline).
Standardized to align with Purchase Status Report Excel specifications.
"""

from __future__ import annotations
import os
import re
import pandas as pd
import numpy as np


def clean_num(series) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    return pd.to_numeric(series.astype(str).str.replace(',', '').str.strip(), errors='coerce')


def safe_parse_date(series) -> pd.Series:
    if series is None:
        return pd.Series(dtype='datetime64[ns]')
    return pd.to_datetime(series, dayfirst=True, errors='coerce')


def find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    aliases_set = {a.lower().strip() for a in aliases}
    for col in df.columns:
        if str(col).lower().strip() in aliases_set:
            return col
    return None


def compute_po_missing(df_grpo: pd.DataFrame | None) -> dict:
    TARGET_COLS = [
        'Gate Entry No', 'PO Number', 'GRPO No', 'Series Name', 'Posting Date',
        'Delivery Date', 'Document Date', 'Vendor Ref No', 'Branch', 'Document Status',
        'Canceled Status', 'Group Name', 'Vendor Code', 'Vendor Name', 'Item Group',
        'Item Code', 'Item Description', 'UOM', 'GRPO Qty', 'GRPO Price',
        'Document Currency', 'Document Rate', 'Line Total', 'Document Total',
        'Warehouse Code', 'Account Code'
    ]

    empty_kpis = {
        "total_count": 0,
        "unique_grpo": 0,
        "sum_grpo_qty": "0.00",
        "sum_grpo_value": "₹0.00"
    }

    if df_grpo is None or df_grpo.empty:
        return {
            "foc_items": {"title": "FOC Items Sheet", "kpis": empty_kpis, "columns": TARGET_COLS, "rows": []},
            "job_work": {"title": "Job Work Items Sheet", "kpis": empty_kpis, "columns": TARGET_COLS, "rows": []},
            "repair_maintenance": {"title": "Repair & Maintenance Sheet", "kpis": empty_kpis, "columns": TARGET_COLS, "rows": []},
        }

    grpo = df_grpo.copy()

    for col in TARGET_COLS:
        if col not in grpo.columns:
            found = find_col(grpo, [col])
            if found:
                grpo[col] = grpo[found]
            else:
                grpo[col] = ""

    grpo = grpo[TARGET_COLS].copy()

    grpo['GRPO_Qty_Num'] = clean_num(grpo['GRPO Qty']).fillna(0.0)
    grpo['Line_Total_Num'] = clean_num(grpo['Line Total']).fillna(0.0)

    po_str = grpo['PO Number'].astype(str).str.strip()
    is_po_missing = (
        grpo['PO Number'].isna() | po_str.isin(['', '0', '0.0', 'nan', 'None', '—', '-'])
    )

    missing_df = grpo[is_po_missing].copy()

    for d_col in ['Posting Date', 'Delivery Date', 'Document Date']:
        if d_col in missing_df.columns:
            missing_df[d_col] = safe_parse_date(missing_df[d_col]).apply(lambda dt: dt.strftime('%Y-%m-%d') if pd.notna(dt) else "")

    def format_kpis(subset_df: pd.DataFrame) -> dict:
        total_count = len(subset_df)
        unique_grpo = int(subset_df['GRPO No'].nunique()) if not subset_df.empty else 0
        sum_qty = float(subset_df['GRPO_Qty_Num'].sum()) if not subset_df.empty else 0.0
        sum_val = float(subset_df['Line_Total_Num'].sum()) if not subset_df.empty else 0.0

        if sum_val >= 1e7:
            val_str = f"₹{(sum_val / 1e7):.2f} Cr"
        elif sum_val >= 1e5:
            val_str = f"₹{(sum_val / 1e5):.2f} Lakh"
        else:
            val_str = f"₹{sum_val:,.2f}"

        return {
            "total_count": total_count,
            "unique_grpo": unique_grpo,
            "sum_grpo_qty": f"{sum_qty:,.2f}",
            "sum_grpo_value": val_str,
        }

    # 1. FOC Items Sheet (Series Name starts with FOC)
    foc_mask = missing_df['Series Name'].astype(str).str.strip().str.upper().str.startswith('FOC')
    foc_df = missing_df[foc_mask]

    # 2. Job Work Items Sheet (Group Name == 'JOB WORK VENDOR')
    jw_mask = missing_df['Group Name'].astype(str).str.strip().str.upper() == 'JOB WORK VENDOR'
    jw_df = missing_df[jw_mask]

    # 3. Repair & Maintenance Items Sheet (Item Group == 'Rep & Maint Mach')
    rep_mask = missing_df['Item Group'].astype(str).str.strip() == 'Rep & Maint Mach'
    rep_df = missing_df[rep_mask]

    foc_kpis = format_kpis(foc_df)
    jw_kpis = format_kpis(jw_df)
    rep_kpis = format_kpis(rep_df)

    foc_rows = foc_df[TARGET_COLS].to_dict(orient="records")
    jw_rows = jw_df[TARGET_COLS].to_dict(orient="records")
    rep_rows = rep_df[TARGET_COLS].to_dict(orient="records")

    return {
        "foc_items": {
            "title": "FOC Items Sheet",
            "kpis": foc_kpis,
            "columns": TARGET_COLS,
            "rows": foc_rows,
        },
        "job_work": {
            "title": "Job Work Items Sheet",
            "kpis": jw_kpis,
            "columns": TARGET_COLS,
            "rows": jw_rows,
        },
        "repair_maintenance": {
            "title": "Repair & Maintenance Sheet",
            "kpis": rep_kpis,
            "columns": TARGET_COLS,
            "rows": rep_rows,
        }
    }


def run(dfs_or_df: dict[str, pd.DataFrame] | pd.DataFrame) -> dict:
    if isinstance(dfs_or_df, pd.DataFrame):
        dfs = {"purchase_order": dfs_or_df}
    else:
        dfs = dfs_or_df or {}

    df_po = dfs.get("purchase_order")
    df_grpo = dfs.get("grpo")
    df_holiday = dfs.get("holiday")

    if df_po is None or df_po.empty:
        return {
            "kpis": {},
            "charts": {},
            "po_missing": compute_po_missing(df_grpo),
            "tables": [{"title": "Purchase Order Status — Full Audit Detail", "columns": [], "rows": []}]
        }

    # [Existing processing logic remains...]
    # We will also call compute_po_missing(df_grpo) at the return block!


    # Column mappings in PO Report
    col_po_no = find_col(df_po, ["po no", "po no.", "po number", "purchase order no"]) or 'PO No'
    col_item_code = find_col(df_po, ["item code", "item_code", "item no", "item no."]) or 'Item Code'
    col_post_date = find_col(df_po, ["posting date", "post date", "po date"]) or 'Posting Date'
    col_deliv_date = find_col(df_po, ["delivery date", "deliv date"]) or 'Delivery Date'
    col_doc_date = find_col(df_po, ["document date", "doc date"]) or 'Document Date'
    col_branch = find_col(df_po, ["branch", "plant"]) or 'Branch'
    col_doc_status = find_col(df_po, ["document status", "doc status", "status"]) or 'Document Status'
    col_canceled_status = find_col(df_po, ["canceled status", "canceled", "cancelled status"]) or 'Canceled Status'
    col_vendor_group = find_col(df_po, ["vendor group", "vendor_group"]) or 'Vendor Group'
    col_vendor_code = find_col(df_po, ["vendor code", "card code", "vendor_code"]) or 'Vendor Code'
    col_vendor_name = find_col(df_po, ["vendor name", "card name", "vendor_name"]) or 'Vendor Name'
    col_item_group = find_col(df_po, ["item group", "item_group"]) or 'Item Group'
    col_item_desc = find_col(df_po, ["item description", "description", "item name"]) or 'Item Description'
    col_uom = find_col(df_po, ["uom", "unit"]) or 'UOM'
    col_po_qty = find_col(df_po, ["po qty", "ordered qty", "quantity", "qty"]) or 'PO Qty'
    col_open_qty = find_col(df_po, ["open qty", "outstanding qty"]) or 'Open Qty'
    col_po_price = find_col(df_po, ["po price", "unit price", "price"]) or 'PO Price'
    col_doc_curr = find_col(df_po, ["document currency", "currency"]) or 'Document Currency'
    col_doc_rate = find_col(df_po, ["document rate", "doc rate", "rate"]) or 'Document Rate'
    col_line_total = find_col(df_po, ["line total", "total", "line_total"]) or 'Line Total'
    col_doc_total = find_col(df_po, ["document total", "doc total"]) or 'Document Total'
    col_po_series = find_col(df_po, ["po series", "series"]) or 'PO Series'

    # Column mappings in GRPO Report
    grpo_key_qty = {}
    grpo_key_price = {}
    grpo_key_line_total = {}
    grpo_po_to_grn_no = {}

    if df_grpo is not None and not df_grpo.empty:
        g_po_no = find_col(df_grpo, ["po number", "po no", "po no."]) or 'PO Number'
        g_grn_no = find_col(df_grpo, ["grpo no", "grpo no.", "grn no", "receipt no"]) or 'GRPO No'
        g_item_code = find_col(df_grpo, ["item code", "item_code", "item no."]) or 'Item Code'
        g_qty = find_col(df_grpo, ["grpo qty", "quantity", "received qty"]) or 'GRPO Qty'
        g_price = find_col(df_grpo, ["grpo price", "unit price", "price"]) or 'GRPO Price'
        g_line_tot = find_col(df_grpo, ["line total", "row total", "total"]) or 'Line Total'

        # Clean GRPO numeric
        df_grpo_work = df_grpo.copy()
        df_grpo_work['_qty'] = clean_num(df_grpo_work[g_qty]) if g_qty in df_grpo_work.columns else 0
        df_grpo_work['_price'] = clean_num(df_grpo_work[g_price]) if g_price in df_grpo_work.columns else 0
        df_grpo_work['_line_total'] = clean_num(df_grpo_work[g_line_tot]) if g_line_tot in df_grpo_work.columns else 0

        # Unique key mapping
        g_po_str = df_grpo_work[g_po_no].astype(str).str.strip() if g_po_no in df_grpo_work.columns else ""
        g_item_str = df_grpo_work[g_item_code].astype(str).str.strip() if g_item_code in df_grpo_work.columns else ""
        df_grpo_work['_key'] = g_po_str + "-" + g_item_str

        df_grpo_dedup = df_grpo_work.drop_duplicates(subset=['_key'], keep='first')
        grpo_key_qty = df_grpo_dedup.set_index('_key')['_qty'].to_dict()
        grpo_key_price = df_grpo_dedup.set_index('_key')['_price'].to_dict()
        grpo_key_line_total = df_grpo_dedup.set_index('_key')['_line_total'].to_dict()

        if g_po_no in df_grpo_work.columns and g_grn_no in df_grpo_work.columns:
            df_first_grn = df_grpo_work.dropna(subset=[g_po_no]).drop_duplicates(subset=[g_po_no], keep='first')
            grpo_po_to_grn_no = df_first_grn.set_index(g_po_no)[g_grn_no].to_dict()

    # Holiday mapping
    holiday_map = {}
    if df_holiday is not None and not df_holiday.empty:
        for _, h_row in df_holiday.iterrows():
            d_val = h_row.iloc[-1]
            h_name = h_row.iloc[1] if len(h_row) > 1 else "Public Holiday"
            if pd.notna(d_val):
                d_parsed = pd.to_datetime(d_val, errors='coerce')
                if pd.notna(d_parsed):
                    holiday_map[d_parsed.date()] = str(h_name).strip()

    # Build Result Dataframe (38 Columns)
    df_res = pd.DataFrame()

    raw_po_no = df_po[col_po_no].astype(str).str.strip() if col_po_no in df_po.columns else pd.Series([""] * len(df_po))
    raw_item_code = df_po[col_item_code].astype(str).str.strip() if col_item_code in df_po.columns else pd.Series([""] * len(df_po))

    df_res['PO No'] = raw_po_no
    df_res['Item Code'] = raw_item_code
    df_res['Key'] = df_res['PO No'] + "-" + df_res['Item Code']
    df_res['GRN No'] = df_res['PO No'].map(grpo_po_to_grn_no).fillna("")

    df_res['PO Series'] = df_po[col_po_series].astype(str).str.strip() if col_po_series in df_po.columns else ""
    df_res['Posting Date'] = safe_parse_date(df_po[col_post_date]) if col_post_date in df_po.columns else None
    df_res['Delivery Date'] = safe_parse_date(df_po[col_deliv_date]) if col_deliv_date in df_po.columns else None
    df_res['Document Date'] = safe_parse_date(df_po[col_doc_date]) if col_doc_date in df_po.columns else None

    df_res['Branch'] = df_po[col_branch].astype(str).str.strip() if col_branch in df_po.columns else ""
    df_res['Document Status'] = df_po[col_doc_status].astype(str).str.strip().str.title() if col_doc_status in df_po.columns else ""
    df_res['Canceled Status'] = df_po[col_canceled_status].astype(str).str.strip() if col_canceled_status in df_po.columns else ""

    df_res['Vendor Group'] = df_po[col_vendor_group].astype(str).str.strip() if col_vendor_group in df_po.columns else ""
    df_res['Vendor Code'] = df_po[col_vendor_code].astype(str).str.strip() if col_vendor_code in df_po.columns else ""
    df_res['Vendor Name'] = df_po[col_vendor_name].astype(str).str.strip() if col_vendor_name in df_po.columns else ""

    df_res['Item Group'] = df_po[col_item_group].astype(str).str.strip() if col_item_group in df_po.columns else ""
    df_res['Item Description'] = df_po[col_item_desc].astype(str).str.strip() if col_item_desc in df_po.columns else ""
    df_res['UOM'] = df_po[col_uom].astype(str).str.strip() if col_uom in df_po.columns else ""

    df_res['PO Qty'] = clean_num(df_po[col_po_qty]).fillna(0) if col_po_qty in df_po.columns else 0.0
    df_res['Open Qty'] = clean_num(df_po[col_open_qty]).fillna(0) if col_open_qty in df_po.columns else 0.0

    # GRN Qty from map
    df_res['GRN Qty'] = df_res['Key'].map(grpo_key_qty)

    # PO Monitoring Status
    def calc_po_mon_status(row):
        if row['Canceled Status'] == 'Yes':
            return 'PO Canceled'
        if pd.isna(row['GRN Qty']):
            return 'Item Not Received'
        if row['PO Qty'] == row['Open Qty'] and row['GRN Qty'] > 0:
            return 'Open Qty Error'
        if row['Document Status'] == 'Closed':
            return 'PO Closed'
        if row['Open Qty'] == 0:
            return 'Fully Received'
        if row['Document Status'] == 'Open' and row['PO Qty'] > row['Open Qty'] and row['Open Qty'] > 0:
            return 'Partially Received'
        return 'Check'

    df_res['PO Monitoring Status'] = df_res.apply(calc_po_mon_status, axis=1)

    # Holiday & Sunday Exception
    def calc_holiday_exc(dt):
        if pd.isna(dt) or dt is None:
            return 'Regular'
        d = dt.date()
        if dt.weekday() == 6:  # Sunday
            return 'Sunday'
        if d in holiday_map:
            return f"Holiday - {holiday_map[d]}"
        return 'Regular'

    df_res['Holiday & Sunday Exception'] = df_res['Posting Date'].apply(calc_holiday_exc)

    # Excess QTY
    df_res['Excess QTY'] = np.where(
        df_res['GRN Qty'].isna(),
        0,
        np.where(df_res['PO Qty'] - df_res['GRN Qty'] < 0, (df_res['PO Qty'] - df_res['GRN Qty']).abs(), 0)
    )

    df_res['Excess Qty Variation %'] = np.where(
        df_res['Excess QTY'] > 0,
        df_res['Excess QTY'] / np.where(df_res['PO Qty'] > 0, df_res['PO Qty'], 1),
        0
    )

    def calc_qty_diff(row):
        if pd.isna(row['GRN Qty']):
            return 'Regular'
        diff = row['PO Qty'] - row['GRN Qty']
        if diff >= 0:
            return 'Regular'
        if row['PO Qty'] > 0 and (abs(diff) / row['PO Qty']) <= 0.05:
            return 'Tolerable'
        return 'Exception'

    df_res['QTY Difference'] = df_res.apply(calc_qty_diff, axis=1)

    # Price fields
    df_res['PO Price'] = clean_num(df_po[col_po_price]).fillna(0) if col_po_price in df_po.columns else 0.0
    df_res['GRN Price'] = df_res['Key'].map(grpo_key_price)

    df_res['Excess Rate'] = np.where(
        df_res['GRN Price'].isna(),
        0,
        np.where(df_res['PO Price'] - df_res['GRN Price'] < 0, (df_res['PO Price'] - df_res['GRN Price']).abs(), 0)
    )

    df_res['Excess Rate Variation %'] = np.where(
        df_res['Excess Rate'] > 0,
        df_res['Excess Rate'] / np.where(df_res['PO Price'] > 0, df_res['PO Price'], 1),
        0
    )

    def calc_rate_diff(row):
        if pd.isna(row['GRN Price']):
            return 'Regular'
        diff = row['PO Price'] - row['GRN Price']
        if diff >= 0:
            return 'Regular'
        if row['PO Price'] > 0 and (abs(diff) / row['PO Price']) <= 0.05:
            return 'Tolerable'
        return 'Exception'

    df_res['Rate Difference'] = df_res.apply(calc_rate_diff, axis=1)

    df_res['Document Currency'] = df_po[col_doc_curr].astype(str).str.strip() if col_doc_curr in df_po.columns else 'INR'
    df_res['Document Rate'] = clean_num(df_po[col_doc_rate]).fillna(1) if col_doc_rate in df_po.columns else 1.0

    po_line_tot_calc = df_res['PO Qty'] * df_res['PO Price']
    raw_line_tot = clean_num(df_po[col_line_total]) if col_line_total in df_po.columns else po_line_tot_calc
    df_res['Line Total'] = raw_line_tot.fillna(po_line_tot_calc)

    df_res['GRN Line Total'] = df_res['Key'].map(grpo_key_line_total)

    df_res['Excess Price'] = np.where(
        df_res['GRN Line Total'].isna(),
        0,
        np.where(df_res['Line Total'] - df_res['GRN Line Total'] < 0, (df_res['Line Total'] - df_res['GRN Line Total']).abs(), 0)
    )

    df_res['Excess Price Variation %'] = np.where(
        df_res['Excess Price'] > 0,
        df_res['Excess Price'] / np.where(df_res['Line Total'] > 0, df_res['Line Total'], 1),
        0
    )

    def calc_line_diff(row):
        if pd.isna(row['GRN Line Total']):
            return 'Regular'
        diff = row['Line Total'] - row['GRN Line Total']
        if diff >= 0:
            return 'Regular'
        if row['Line Total'] > 0 and (abs(diff) / row['Line Total']) <= 0.05:
            return 'Tolerable'
        return 'Exception'

    df_res['Line Total Difference'] = df_res.apply(calc_line_diff, axis=1)
    df_res['Document Total'] = clean_num(df_po[col_doc_total]).fillna(0) if col_doc_total in df_po.columns else 0.0

    # ── Calculate exact 12 KPIs ──────────────────────────────────────────────
    valid_po_mask = (df_res['PO No'] != '') & (df_res['PO No'] != '0') & (df_res['PO No'].notna())

    unique_po_count = int(df_res[valid_po_mask]['PO No'].nunique())
    total_po_val_cr = round(float(df_res['Line Total'].sum()) / 10000000.0, 2)
    canceled_po_count = int(df_res[valid_po_mask & (df_res['Canceled Status'] == 'Yes')]['PO No'].nunique())

    holiday_po_mask = valid_po_mask & (~df_res['Holiday & Sunday Exception'].isin(['Sunday', 'Regular']))
    holiday_po_count = int(df_res[holiday_po_mask]['PO No'].nunique())

    sunday_po_mask = valid_po_mask & (df_res['Holiday & Sunday Exception'] == 'Sunday')
    sunday_po_count = int(df_res[sunday_po_mask]['PO No'].nunique())

    cnt_excess_qty = int((df_res['QTY Difference'] == 'Exception').sum())
    sum_excess_qty_lakh = round(float(df_res[df_res['QTY Difference'] == 'Exception']['Excess QTY'].sum()) / 100000.0, 2)

    cnt_excess_rate = int((df_res['Rate Difference'] == 'Exception').sum())
    exc_rate_rows = df_res[df_res['Rate Difference'] == 'Exception']
    sum_excess_rate = round(float((exc_rate_rows['Excess Rate'] * exc_rate_rows['Document Rate']).sum()), 2)

    cnt_excess_price = int((df_res['Line Total Difference'] == 'Exception').sum())
    sum_excess_price_lakh = round(float(df_res[df_res['Line Total Difference'] == 'Exception']['Excess Price'].sum()) / 100000.0, 2)

    kpi_contract = {
        "foreign_vendor": "FILTER",
        "unique_po_raise": unique_po_count,
        "total_po_value": f"{total_po_val_cr:.2f} Cr",
        "canceled_po_count": canceled_po_count,
        "holiday_exception": holiday_po_count,
        "sunday_exception": sunday_po_count,
        "count_of_excess_qty": cnt_excess_qty,
        "sum_of_excess_qty": f"{sum_excess_qty_lakh:.2f} Lakh",
        "count_of_excess_rate": cnt_excess_rate,
        "sum_of_excess_rate": float(sum_excess_rate),
        "count_of_excess_price": cnt_excess_price,
        "sum_of_excess_price": f"{sum_excess_price_lakh:.2f} Lakh",
    }

    total_lines = len(df_res)
    open_mask = df_res['Document Status'] == 'Open'
    closed_mask = df_res['Document Status'] == 'Closed'

    open_lines = int(open_mask.sum())
    closed_lines = int(closed_mask.sum())

    open_line_pct = round((open_lines / total_lines) * 100, 1) if total_lines else 0.0
    closed_line_pct = round((closed_lines / total_lines) * 100, 1) if total_lines else 0.0

    total_val = float(df_res['Line Total'].sum())
    open_val = float(df_res[open_mask]['Line Total'].sum())
    closed_val = float(df_res[closed_mask]['Line Total'].sum())

    open_val_cr = round(open_val / 1e7, 2)
    closed_val_cr = round(closed_val / 1e7, 2)

    open_val_pct = round((open_val / total_val) * 100) if total_val else 0
    closed_val_pct = round((closed_val / total_val) * 100) if total_val else 0

    charts_contract = {
        "po_status_distribution": {
            "total_lines": total_lines,
            "open_lines": open_lines,
            "open_line_pct": open_line_pct,
            "closed_lines": closed_lines,
            "closed_line_pct": closed_line_pct,
        },
        "po_value_exposure": {
            "total_value": f"{total_val/1e7:.2f} Cr",
            "closed_value": f"{closed_val_cr:.2f} Cr",
            "closed_value_pct": closed_val_pct,
            "open_value": f"{open_val_cr:.2f} Cr",
            "open_value_pct": open_val_pct,
        }
    }

    # Format dates as YYYY-MM-DD for JSON serialization
    for date_col in ['Posting Date', 'Delivery Date', 'Document Date']:
        df_res[date_col] = df_res[date_col].apply(lambda dt: dt.strftime('%Y-%m-%d') if pd.notna(dt) else "")

    # Convert DataFrame to records dict
    table_rows = df_res.to_dict(orient="records")

    columns_list = list(df_res.columns)

    return {
        "kpis": kpi_contract,
        "charts": charts_contract,
        "po_missing": compute_po_missing(df_grpo),
        "tables": [
            {
                "title": "Purchase Order Status — Full Audit Detail",
                "columns": columns_list,
                "rows": table_rows
            }
        ]
    }
