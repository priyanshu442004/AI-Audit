"""
Module B — Gate Entry Date Integrity.

Rule: Vendor Bill Date ≤ GE Date ≤ GRPO Date ≤ AP Date.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import warnings

# Suppress pandas mixed-format date parsing warnings
warnings.simplefilter(action='ignore', category=UserWarning)

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
    val_str = str(val).strip().upper()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_str_val(val, default="—") -> str:
    if pd.isna(val) or val is None:
        return default
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", "null", ""):
        return default
    return val_str

def parse_single_date(val) -> pd.Timestamp | None:
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", ""):
        return None
    try:
        dt = pd.to_datetime(val_str, errors='coerce', dayfirst=True)
        if pd.notna(dt):
            return dt
    except:
        pass
    return None


def run(dfs_or_ge: dict[str, pd.DataFrame] | pd.DataFrame, df_grpo_raw: pd.DataFrame = None) -> dict:
    # Support both dict and DataFrame for backward compatibility (tests vs production)
    df_po_raw = None
    if isinstance(dfs_or_ge, dict):
        dfs = dfs_or_ge
        df_ge_raw = dfs.get("gate_entry")
        df_grpo_raw = dfs.get("grpo")
        df_ap_raw = dfs.get("ap_invoice_report")
        if df_ap_raw is None or df_ap_raw.empty:
            df_ap_raw = dfs.get("purchase_register")
        df_po_raw = dfs.get("purchase_order")
    else:
        df_ge_raw = dfs_or_ge
        df_ap_raw = None

    if df_ge_raw is None or df_ge_raw.empty:
        return {
            "kpis": {
                "gate_entries": 0,
                "grpo_docs": 0,
                "exceptions": 0,
                "integrity_pct": 100.0,
                "missing_grpo_date": 0,
                "missing_bill_date": 0,
                "ge_lt_grpo": 0,
                "ge_eq_grpo": 0,
            },
            "charts": {
                "pass_vs_exception": {
                    "total": 0,
                    "integrity_pct": 100.0,
                    "segments": [
                        {"label": "Pass", "value": 0, "dash": 0, "offset": 0},
                        {"label": "Exception", "value": 0, "dash": 0, "offset": 0},
                    ],
                },
                "detailed_checks": [],
            },
            "tables": [
                {"title": "GE > GRPO Date Exceptions", "rows": []},
                {"title": "Gate Entry Full Transaction List", "rows": []},
            ],
        }

    # ── Gate Entry Column Detection ──────────────────────────────────────────
    col_ge_no = find_col(df_ge_raw, ["gate entry no", "gate entry no.", "ge no", "ge no.", "gate entry number", "security entry no", "security entry number"])
    col_ge_date = find_col(df_ge_raw, ["ge date", "gate entry date", "entry date", "security date"])
    col_ge_po_no = find_col(df_ge_raw, ["purchase order number", "purchase order no", "po number", "po no", "po no.", "purchase order", "po_no", "pono"])
    col_ge_vendor_code = find_col(df_ge_raw, ["vendor code", "bp code", "supplier code", "vendorcode", "bpcode", "account code", "vendor"])
    col_ge_vendor_name = find_col(df_ge_raw, ["vendor name", "bp name", "supplier name", "vendorname", "bpname", "account name", "accountname", "party name", "name", "vendorname"])
    col_ge_vendor_bill_no = find_col(df_ge_raw, ["vendor bill no", "bill no", "supplier invoice no", "vendor inv no", "vendorbillno"])
    col_ge_vendor_bill_date = find_col(df_ge_raw, ["vendor bill date", "bill date", "supplier invoice date", "vendor inv date", "vend bill date"])
    col_ge_transporter = find_col(df_ge_raw, ["transporter", "transporter name", "transportername", "carrier"])
    col_ge_grpo_no = find_col(df_ge_raw, ["grpo no", "grpo no.", "linked grpo", "base grpo no", "grpo number", "ge_grpo_no", "grn", "grn no", "grn no.", "grn number", "goods receipt no", "goods receipt number"])

    # ── GRPO Column Detection ────────────────────────────────────────────────
    col_grpo_ge_no = None
    col_grpo_po_no = None
    col_grpo_no = None
    col_grpo_date = None
    col_grpo_qty = None
    col_grpo_rate = None
    col_grpo_line_total = None
    col_grpo_vendor_code = None
    col_grpo_vendor_name = None
    col_grpo_vendor_ref = None
    col_grpo_item_code = None
    col_grpo_item_desc = None
    col_grpo_item_group = None
    col_grpo_currency = None

    if df_grpo_raw is not None and not df_grpo_raw.empty:
        col_grpo_ge_no = find_col(df_grpo_raw, ["gate entry no", "ge no", "gate entry number", "gateentryno", "security entry no", "linked gate entry", "gate no", "entry no"])
        col_grpo_po_no = find_col(df_grpo_raw, ["po number", "po no", "po no.", "purchase order number", "purchase order no", "purchase order", "po_no", "pono", "base ref", "baseref", "base ref.", "base_ref"])
        col_grpo_no = find_col(df_grpo_raw, ["grpo no", "grpo no.", "receipt no", "receipt number", "grpono", "goods receipt no", "grpo number", "grn", "grn no", "grn no.", "grn number"])
        col_grpo_date = find_col(df_grpo_raw, ["posting date", "document date", "doc date", "docdate", "date", "grpo date", "receipt date"])
        col_grpo_qty = find_col(df_grpo_raw, ["po qty", "grpo qty", "received qty", "quantity", "qty", "received quantity"])
        col_grpo_rate = find_col(df_grpo_raw, ["po price", "grpo rate", "unit price", "price", "rate", "item price", "unit cost"])
        col_grpo_line_total = find_col(df_grpo_raw, ["line total", "linetotal", "line amount", "u_total", "total"])
        col_grpo_vendor_code = find_col(df_grpo_raw, ["vendor code", "bp code", "supplier code", "vendorcode", "bpcode", "account code", "vendor", "cardcode", "card code"])
        col_grpo_vendor_name = find_col(df_grpo_raw, ["vendor name", "bp name", "supplier name", "vendorname", "bpname", "account name", "accountname", "party name", "name", "cardname", "card name"])
        col_grpo_vendor_ref = find_col(df_grpo_raw, ["vendor ref no", "vendor ref. no", "vendor ref. no.", "vendor ref no.", "vendor bill no", "bill no", "supplier invoice no", "vendor inv no", "vendorbillno", "numatcard", "num at card"])
        col_grpo_item_code = find_col(df_grpo_raw, ["item code", "item_code", "item no", "item no.", "itemno", "material no", "itemcode"])
        col_grpo_item_desc = find_col(df_grpo_raw, ["item description", "description", "material description", "part description", "item name", "itemdescription", "dscription"])
        col_grpo_item_group = find_col(df_grpo_raw, ["item group", "item_group", "group name", "groupname", "itmsgrpcod", "itms grpcod"])
        col_grpo_currency = find_col(df_grpo_raw, ["document currency", "currency", "doc currency"])

    # ── AP Column Detection ──────────────────────────────────────────────────
    col_ap_po_no = None
    col_ap_grpo_no = None
    col_ap_inv_no = None
    col_ap_date = None
    col_ap_inv_qty = None
    col_ap_line_total = None
    if df_ap_raw is not None and not df_ap_raw.empty:
        col_ap_po_no = find_col(df_ap_raw, ["po number", "po no", "po no.", "purchase order number", "purchase order no", "purchase order", "po_no", "pono"])
        col_ap_grpo_no = find_col(df_ap_raw, ["grpo number", "grpo no", "grpo no.", "grpo_number", "grpo no.", "grn", "grn no", "grn no.", "grn number", "receipt no", "receipt number"])
        col_ap_inv_no = find_col(df_ap_raw, ["ap invoice no", "ap invoice no.", "invoice no", "invoice no.", "ap_invoice_no", "ap invoice number"])
        col_ap_date = find_col(df_ap_raw, ["posting date", "document date", "doc date", "docdate", "date", "invoice date", "inv date", "ap date"])
        col_ap_inv_qty = find_col(df_ap_raw, ["invoice qty", "invoice quantity", "qty", "quantity", "invoice_qty"])
        col_ap_line_total = find_col(df_ap_raw, ["line total", "linetotal", "line amount", "u_total", "total"])

    # ── Pre-aggregate GRPO Lookups ───────────────────────────────────────────
    grpo_lookup = {}
    grpo_by_no = {}
    grpo_by_po = {}
    if df_grpo_raw is not None and not df_grpo_raw.empty:
        if col_grpo_date:
            df_grpo_raw["parsed_grpo_date"] = pd.to_datetime(df_grpo_raw[col_grpo_date], errors='coerce', dayfirst=True)
        else:
            df_grpo_raw["parsed_grpo_date"] = pd.NaT
        if col_grpo_ge_no:
            for _, row in df_grpo_raw.iterrows():
                ge_raw = row.get(col_grpo_ge_no)
                ge_list = [normalize_id(g) for g in str(ge_raw).split(",") if normalize_id(g)] if pd.notna(ge_raw) else []
                po_raw = row.get(col_grpo_po_no) if col_grpo_po_no else None
                po_list = [normalize_id(p) for p in str(po_raw).split(",") if normalize_id(p)] if pd.notna(po_raw) else []
                
                for ge_val in ge_list:
                    if not po_list:
                        key = (ge_val, "")
                        if key not in grpo_lookup:
                            grpo_lookup[key] = []
                        grpo_lookup[key].append(row)
                    for po_val in po_list:
                        key = (ge_val, po_val)
                        if key not in grpo_lookup:
                            grpo_lookup[key] = []
                        grpo_lookup[key].append(row)
        
        if col_grpo_no:
            for _, row in df_grpo_raw.iterrows():
                g_no = normalize_id(row.get(col_grpo_no))
                if g_no:
                    if g_no not in grpo_by_no:
                        grpo_by_no[g_no] = []
                    grpo_by_no[g_no].append(row)

        if col_grpo_po_no:
            for _, row in df_grpo_raw.iterrows():
                p_no = normalize_id(row.get(col_grpo_po_no))
                if p_no:
                    if p_no not in grpo_by_po:
                        grpo_by_po[p_no] = []
                    grpo_by_po[p_no].append(row)

    # ── Pre-aggregate AP Lookup ───────────────────────────────────────────────
    ap_lookup = {}
    if df_ap_raw is not None and not df_ap_raw.empty and col_ap_po_no and col_ap_grpo_no:
        for _, row in df_ap_raw.iterrows():
            po_raw = row.get(col_ap_po_no)
            po_list = [normalize_id(p) for p in str(po_raw).split(",") if normalize_id(p)] if pd.notna(po_raw) else []
            grpo_raw = row.get(col_ap_grpo_no)
            grpo_list = [normalize_id(g) for g in str(grpo_raw).split(",") if normalize_id(g)] if pd.notna(grpo_raw) else []
            
            for po_val in po_list:
                for grpo_val in grpo_list:
                    key = (po_val, grpo_val)
                    if key not in ap_lookup:
                        ap_lookup[key] = []
                    ap_lookup[key].append(row)
                    
                    key_grpo_only = ("", grpo_val)
                    if key_grpo_only not in ap_lookup:
                        ap_lookup[key_grpo_only] = []
                    ap_lookup[key_grpo_only].append(row)

    # ── Process Gate Entry Records ───────────────────────────────────────────
    records = []
    exceptions_rows = []
    
    ge_lt_grpo_cnt = 0
    ge_eq_grpo_cnt = 0
    ge_gt_grpo_cnt = 0
    missing_grpo_date_cnt = 0
    missing_bill_date_cnt = 0
    total_ge = len(df_ge_raw)

    po_currency_lookup = {}
    if df_po_raw is not None and not df_po_raw.empty:
        col_po_no = find_col(df_po_raw, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
        col_po_currency = find_col(df_po_raw, ["document currency", "currency", "doc currency", "po currency"])
        if col_po_no and col_po_currency:
            for _, row_po in df_po_raw.iterrows():
                po_val = normalize_id(row_po.get(col_po_no))
                if po_val:
                    po_currency_lookup[po_val] = str(row_po.get(col_po_currency, "")).strip()

    df_ge_raw["parsed_ge_date"] = pd.to_datetime(df_ge_raw[col_ge_date], errors='coerce', dayfirst=True) if col_ge_date else pd.NaT
    df_ge_raw["parsed_v_bill_date"] = pd.to_datetime(df_ge_raw[col_ge_vendor_bill_date], errors='coerce', dayfirst=True) if col_ge_vendor_bill_date else pd.NaT

    valid_pos = set()
    if df_po_raw is not None and not df_po_raw.empty:
        col_po_no = find_col(df_po_raw, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
        if col_po_no:
            valid_pos = {normalize_id(x) for x in df_po_raw[col_po_no].dropna()}

    for _, row in df_ge_raw.iterrows():
        ge_no_raw = row.get(col_ge_no)
        ge_no = normalize_id(ge_no_raw)
        
        # Strict checking: skip if ge_no is blank or null
        if not ge_no or ge_no.lower() in ("nan", "none", "null"):
            continue
            
        ge_date_val = row.get("parsed_ge_date")
        ge_date = ge_date_val if pd.notna(ge_date_val) else None
        
        po_no_raw = row.get(col_ge_po_no) if col_ge_po_no else None
        po_no = normalize_id(po_no_raw)
        
        # Strictly validate PO number against Purchase Order Report
        if po_no and valid_pos and po_no not in valid_pos:
            po_no = ""
        
        # Vendor Bill Date
        v_bill_date_val = row.get("parsed_v_bill_date")
        v_bill_date = v_bill_date_val if pd.notna(v_bill_date_val) else None
        if not v_bill_date:
            missing_bill_date_cnt += 1
            
        # 1. Lookup GRPO
        matched_grpos = []
        
        # A. Try matching by GRPO Number (col_ge_grpo_no)
        if col_ge_grpo_no:
            ge_grpo_val = normalize_id(row.get(col_ge_grpo_no))
            if ge_grpo_val:
                candidate_grpos = grpo_by_no.get(ge_grpo_val, [])
                if po_no:
                    matched_grpos = [r for r in candidate_grpos if normalize_id(r.get(col_grpo_po_no)) == po_no]
                if not matched_grpos:
                    matched_grpos = candidate_grpos
                    
        # B. Try matching by Gate Entry Number in GRPO (col_grpo_ge_no)
        if not matched_grpos and col_grpo_ge_no:
            matched_grpos = grpo_lookup.get((ge_no, po_no))
            if not matched_grpos:
                matched_grpos = grpo_lookup.get((ge_no, ""))
                
        # C. Fallback to matching by PO Number only
        if not matched_grpos and po_no:
            matched_grpos = grpo_by_po.get(po_no, [])

        if not matched_grpos:
            matched_grpos = []

        def fmt_dt(dt):
            return dt.strftime("%d/%m/%y") if dt else "—"

        if matched_grpos:
            for r_grpo in matched_grpos:
                g_no = normalize_id(r_grpo.get(col_grpo_no))
                grpo_date_val = r_grpo.get("parsed_grpo_date")
                grpo_date = grpo_date_val if pd.notna(grpo_date_val) else None
                
                # Fetch AP Invoices matching this po_no and g_no
                matched_aps = []
                if g_no:
                    ap_list = ap_lookup.get((po_no, g_no))
                    if not ap_list:
                        ap_list = ap_lookup.get(("", g_no))
                    if ap_list:
                        matched_aps = ap_list

                ap_numbers = []
                for r_ap in matched_aps:
                    a_no = normalize_id(r_ap.get(col_ap_inv_no))
                    if a_no and a_no not in ap_numbers:
                        ap_numbers.append(a_no)

                if not ap_numbers:
                    ap_numbers = ["—"]

                # Vendor Country logic
                currency = str(r_grpo.get(col_grpo_currency, "")).strip() if col_grpo_currency else ""
                if not currency:
                    currency = po_currency_lookup.get(po_no, "")
                vendor_country = "India" if currency.upper() in ("INR", "") else "USA"

                # Days(GRPO-GE)
                days_val = "—"
                is_exc = 0
                exceeds_3 = 0
                if grpo_date and ge_date:
                    days_val = int((grpo_date - ge_date).days)
                    if days_val < 0:
                        is_exc = 1
                        ge_gt_grpo_cnt += 1
                    elif days_val > 0:
                        ge_lt_grpo_cnt += 1
                    else:
                        ge_eq_grpo_cnt += 1
                    
                    if days_val > 3:
                        exceeds_3 = 1
                else:
                    missing_grpo_date_cnt += 1

                qty_val = parse_numeric_val(r_grpo.get(col_grpo_qty)) if col_grpo_qty else 0.0
                rate_val = parse_numeric_val(r_grpo.get(col_grpo_rate)) if col_grpo_rate else 0.0
                value_val = parse_numeric_val(r_grpo.get(col_grpo_line_total)) if col_grpo_line_total else 0.0

                # Vendor fallbacks
                v_code = clean_str_val(r_grpo.get(col_grpo_vendor_code, "")) if col_grpo_vendor_code else "—"
                if v_code == "—" and col_ge_vendor_code:
                    v_code = clean_str_val(row.get(col_ge_vendor_code, ""))
                    
                v_name = clean_str_val(r_grpo.get(col_grpo_vendor_name, "")) if col_grpo_vendor_name else "—"
                if v_name == "—" and col_ge_vendor_name:
                    v_name = clean_str_val(row.get(col_ge_vendor_name, ""))

                v_bill_no = clean_str_val(r_grpo.get(col_grpo_vendor_ref, "")) if col_grpo_vendor_ref else "—"
                if v_bill_no == "—" and col_ge_vendor_bill_no:
                    v_bill_no = clean_str_val(row.get(col_ge_vendor_bill_no, ""))

                for a_no in ap_numbers:
                    rec = {
                        "Gate Entry number": ge_no,
                        "Gate Entry Date": fmt_dt(ge_date),
                        "PO Number": po_no if po_no else "—",
                        "GRN Number": g_no if g_no else "—",
                        "AP Invoice Number": a_no,
                        "GRPO Date": fmt_dt(grpo_date),
                        "Vendor Code": v_code,
                        "Vendor Name": v_name,
                        "Vendor Country": vendor_country,
                        "Vendor Bill Number": v_bill_no,
                        "Item Code": clean_str_val(r_grpo.get(col_grpo_item_code, "")),
                        "Item Description": clean_str_val(r_grpo.get(col_grpo_item_desc, "")),
                        "Item Group": clean_str_val(r_grpo.get(col_grpo_item_group, "")),
                        "Quantity": qty_val,
                        "Rate(INR)": rate_val,
                        "Value(INR)": value_val,
                        "Days(GRPO-GE)": days_val,
                        "Seq Exception(GE>GRPO)": is_exc,
                        "Exceeds 3 days": exceeds_3
                    }
                    records.append(rec)
                    
                    if is_exc == 1:
                        exceptions_rows.append({
                            "GE No": ge_no,
                            "GE Date": fmt_dt(ge_date),
                            "GRPO Date": fmt_dt(grpo_date),
                            "Vendor Bill Date": fmt_dt(v_bill_date),
                            "Vendor Bill No": v_bill_no,
                            "Vendor Code": v_code,
                            "GRPO No": g_no,
                        })
        else:
            missing_grpo_date_cnt += 1
            currency = po_currency_lookup.get(po_no, "")
            vendor_country = "India" if currency.upper() in ("INR", "") else "USA"
            
            rec = {
                "Gate Entry number": ge_no,
                "Gate Entry Date": fmt_dt(ge_date),
                "PO Number": po_no if po_no else "—",
                "GRN Number": "—",
                "AP Invoice Number": "—",
                "GRPO Date": "—",
                "Vendor Code": clean_str_val(row.get(col_ge_vendor_code, "")),
                "Vendor Name": clean_str_val(row.get(col_ge_vendor_name, "")),
                "Vendor Country": vendor_country,
                "Vendor Bill Number": clean_str_val(row.get(col_ge_vendor_bill_no, "")),
                "Item Code": "—",
                "Item Description": "—",
                "Item Group": "—",
                "Quantity": 0.0,
                "Rate(INR)": 0.0,
                "Value(INR)": 0.0,
                "Days(GRPO-GE)": "—",
                "Seq Exception(GE>GRPO)": 0,
                "Exceeds 3 days": 0
            }
            records.append(rec)

    # Calculations for KPIs & Charts
    total_lines = len(records)
    total_val = sum(r["Value(INR)"] for r in records)
    seq_exceptions = sum(1 for r in records if r["Seq Exception(GE>GRPO)"] == 1)
    exceeds_3_days = sum(1 for r in records if r["Exceeds 3 days"] == 1)
    
    unique_pos = len(set(r["PO Number"] for r in records if r["PO Number"] and r["PO Number"] != "—"))
    unique_grns = len(set(r["GRN Number"] for r in records if r["GRN Number"] and r["GRN Number"] != "—"))
    unique_aps = len(set(r["AP Invoice Number"] for r in records if r["AP Invoice Number"] and r["AP Invoice Number"] != "—"))
    
    unique_po_flagged = len(set(r["PO Number"] for r in records if r["Seq Exception(GE>GRPO)"] == 1 and r["PO Number"] and r["PO Number"] != "—"))
    unique_grn_flagged = len(set(r["GRN Number"] for r in records if r["Seq Exception(GE>GRPO)"] == 1 and r["GRN Number"] and r["GRN Number"] != "—"))

    pass_count = total_lines - seq_exceptions
    integrity_pct = round(pass_count / total_lines * 100, 2) if total_lines else 0.0
    
    CIRC = 314.0
    pass_dash = round(pass_count / total_lines * CIRC, 0) if total_lines else 0
    exc_dash  = round(seq_exceptions / total_lines * CIRC, 0) if total_lines else 0

    return {
        "kpis": {
            "gate_entries": total_ge,
            "gate_entry_grpo_lines": total_lines,
            "total_value_inr": total_val,
            "sequence_exceptions": seq_exceptions,
            "exceeds_3_day_window": exceeds_3_days,
            "unique_po_numbers": unique_pos,
            "unique_grn_numbers": unique_grns,
            "unique_ap_invoices": unique_aps,
            "unique_po_flagged": unique_po_flagged,
            "unique_grn_flagged": unique_grn_flagged,
            "integrity_pct": integrity_pct,
            "exceptions": seq_exceptions,
            "missing_grpo_date": missing_grpo_date_cnt,
            "missing_bill_date": missing_bill_date_cnt,
        },
        "charts": {
            "pass_vs_exception": {
                "total": total_lines,
                "integrity_pct": integrity_pct,
                "segments": [
                    {"label": "Pass",      "value": pass_count, "dash": pass_dash, "offset": 0},
                    {"label": "Exception", "value": seq_exceptions, "dash": exc_dash,  "offset": -pass_dash},
                ],
            },
            "detailed_checks": [
                {"label": "Total",             "value": total_lines,         "pct": 100},
                {"label": "GE = GRPO (same)",  "value": ge_eq_grpo_cnt,       "pct": round(ge_eq_grpo_cnt / total_lines * 100, 1) if total_lines else 0},
                {"label": "GE < GRPO (normal)","value": ge_lt_grpo_cnt,       "pct": round(ge_lt_grpo_cnt / total_lines * 100, 1) if total_lines else 0},
                {"label": "GE > GRPO (error)", "value": ge_gt_grpo_cnt,       "pct": round(ge_gt_grpo_cnt / total_lines * 100, 1) if total_lines else 0},
                {"label": "Missing GRPO Date", "value": missing_grpo_date_cnt,"pct": round(missing_grpo_date_cnt / total_lines * 100, 1) if total_lines else 0},
                {"label": "Missing Bill Date", "value": missing_bill_date_cnt,"pct": round(missing_bill_date_cnt / total_lines * 100, 1) if total_lines else 0},
            ],
        },
        "tables": [
            {"title": "GE > GRPO Date Exceptions",   "rows": exceptions_rows},
            {"title": "Gate Entry Full Transaction List", "rows": records},
        ],
    }
