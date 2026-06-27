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


def po_overlap(po_str1: str, po_str2: str) -> bool:
    if not po_str1 or not po_str2:
        return False
    parts1 = {normalize_id(p) for p in str(po_str1).split(",") if normalize_id(p)}
    parts2 = {normalize_id(p) for p in str(po_str2).split(",") if normalize_id(p)}
    return bool(parts1.intersection(parts2))


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
    col_grpo_doc_rate = None

    if df_grpo_raw is not None and not df_grpo_raw.empty:
        col_grpo_ge_no = find_col(df_grpo_raw, ["gate entry no", "ge no", "gate entry number", "gateentryno", "security entry no", "linked gate entry", "gate no", "entry no"])
        col_grpo_po_no = find_col(df_grpo_raw, ["po number", "po no", "po no.", "purchase order number", "purchase order no", "purchase order", "po_no", "pono", "base ref", "baseref", "base ref.", "base_ref"])
        col_grpo_no = find_col(df_grpo_raw, ["grpo no", "grpo no.", "receipt no", "receipt number", "grpono", "goods receipt no", "grpo number", "grn", "grn no", "grn no.", "grn number"])
        col_grpo_date = find_col(df_grpo_raw, ["document date", "doc date", "docdate", "posting date", "date", "grpo date", "receipt date"])
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
        col_grpo_doc_rate = find_col(df_grpo_raw, ["document rate", "doc rate", "rate", "documentrate"])

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
                po_raw = row.get(col_grpo_po_no)
                po_list = [normalize_id(p) for p in str(po_raw).split(",") if normalize_id(p)] if pd.notna(po_raw) else []
                for p_no in po_list:
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

    # ── Pre-aggregate PO Lookup for Item Details, Quantity, Rate, Value ────────
    po_items_lookup = {}
    col_po_vendor_code = None
    col_po_vendor_name = None
    col_po_item = None
    col_po_desc = None
    col_po_group = None
    col_po_qty = None
    col_po_price = None
    col_po_rate = None
    col_po_total = None
    
    if df_po_raw is not None and not df_po_raw.empty:
        col_po_no = find_col(df_po_raw, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
        col_po_vendor_code = find_col(df_po_raw, ["vendor code", "vendor_code", "card code", "cardcode"])
        col_po_vendor_name = find_col(df_po_raw, ["vendor name", "vendor_name", "card name", "cardname"])
        col_po_item = find_col(df_po_raw, ["item code", "item_code", "item no", "item no.", "itemno"])
        col_po_desc = find_col(df_po_raw, ["item description", "description", "item_description"])
        col_po_group = find_col(df_po_raw, ["item group", "item_group", "group name"])
        col_po_qty = find_col(df_po_raw, ["po qty", "ordered qty", "quantity", "qty", "po_qty"])
        col_po_price = find_col(df_po_raw, ["po price", "unit price", "price", "rate", "po_price"])
        col_po_rate = find_col(df_po_raw, ["document rate", "doc rate", "rate", "documentrate"])
        col_po_total = find_col(df_po_raw, ["line total", "linetotal", "total", "line_total"])
        
        if col_po_no:
            for _, row_po in df_po_raw.iterrows():
                p_no_raw = row_po.get(col_po_no)
                p_nos = [normalize_id(x) for x in str(p_no_raw).split(",") if normalize_id(x)] if pd.notna(p_no_raw) else []
                for p_no in p_nos:
                    if p_no not in po_items_lookup:
                        po_items_lookup[p_no] = []
                    po_items_lookup[p_no].append(row_po)

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
        po_parts = []
        if po_no_raw and not pd.isna(po_no_raw):
            po_parts = [normalize_id(p) for p in str(po_no_raw).split(",") if normalize_id(p)]
        
        po_no = ", ".join(po_parts) if po_parts else ""
        
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
                if po_parts:
                    matched_grpos = [r for r in candidate_grpos if po_overlap(r.get(col_grpo_po_no), po_no)]
                if not matched_grpos:
                    matched_grpos = candidate_grpos
                    
        # B. Try matching by Gate Entry Number in GRPO (col_grpo_ge_no)
        if not matched_grpos and col_grpo_ge_no:
            if po_parts:
                for p in po_parts:
                    candidates = grpo_lookup.get((ge_no, p))
                    if candidates:
                        matched_grpos.extend(candidates)
            if not matched_grpos:
                matched_grpos = grpo_lookup.get((ge_no, ""), [])
                
        # C. Fallback to matching by PO Number only
        if not matched_grpos and po_parts:
            for p in po_parts:
                candidates = grpo_by_po.get(p)
                if candidates:
                    matched_grpos.extend(candidates)

        # Deduplicate matched GRPOs
        if matched_grpos:
            seen_grpo_ids = set()
            unique_grpos = []
            for r in matched_grpos:
                r_id = id(r)
                if r_id not in seen_grpo_ids:
                    seen_grpo_ids.add(r_id)
                    unique_grpos.append(r)
            matched_grpos = unique_grpos
        else:
            matched_grpos = []

        def fmt_dt(dt):
            return dt.strftime("%d/%m/%y") if dt else "—"

        unique_grns = []
        unique_aps = []
        unique_grpo_dts = []
        days_vals = []
        is_exc = 0
        exceeds_3 = 0
        
        v_code_grpo = "—"
        v_name_grpo = "—"
        v_bill_no_grpo = "—"
        currency = ""
        
        # Item details and values from PO Report
        matched_po_lines = []
        for p in po_parts:
            matched_po_lines.extend(po_items_lookup.get(p, []))
            
        po_item_codes = []
        po_item_descs = []
        po_item_groups = []
        po_qty_sum = 0.0
        po_val_sum = 0.0
        po_rates = []
        
        if matched_po_lines:
            for r_po in matched_po_lines:
                ic = clean_str_val(r_po.get(col_po_item, "")) if col_po_item else "—"
                if ic and ic != "—" and ic not in po_item_codes:
                    po_item_codes.append(ic)
                    
                idsc = clean_str_val(r_po.get(col_po_desc, "")) if col_po_desc else "—"
                if idsc and idsc != "—" and idsc not in po_item_descs:
                    po_item_descs.append(idsc)
                    
                ig = clean_str_val(r_po.get(col_po_group, "")) if col_po_group else "—"
                if ig and ig != "—" and ig not in po_item_groups:
                    po_item_groups.append(ig)
                    
                po_qty = parse_numeric_val(r_po.get(col_po_qty)) if col_po_qty else 0.0
                po_price = parse_numeric_val(r_po.get(col_po_price)) if col_po_price else 0.0
                po_rate_mult = parse_numeric_val(r_po.get(col_po_rate)) if col_po_rate else 1.0
                po_rate_inr = po_price * po_rate_mult
                
                po_qty_sum += po_qty
                line_val = parse_numeric_val(r_po.get(col_po_total)) if col_po_total else (po_qty * po_rate_inr)
                po_val_sum += line_val
                
                if po_rate_inr > 0:
                    po_rate_str = f"{po_rate_inr:.2f}"
                    if po_rate_str not in po_rates:
                        po_rates.append(po_rate_str)
        elif matched_grpos:
            # Fallback to GRPO item details if PO is missing
            for r_grpo in matched_grpos:
                ic = clean_str_val(r_grpo.get(col_grpo_item_code, "")) if col_grpo_item_code else "—"
                if ic and ic != "—" and ic not in po_item_codes:
                    po_item_codes.append(ic)
                    
                idsc = clean_str_val(r_grpo.get(col_grpo_item_desc, "")) if col_grpo_item_desc else "—"
                if idsc and idsc != "—" and idsc not in po_item_descs:
                    po_item_descs.append(idsc)
                    
                ig = clean_str_val(r_grpo.get(col_grpo_item_group, "")) if col_grpo_item_group else "—"
                if ig and ig != "—" and ig not in po_item_groups:
                    po_item_groups.append(ig)
                    
                grpo_qty = parse_numeric_val(r_grpo.get(col_grpo_qty)) if col_grpo_qty else 0.0
                grpo_price = parse_numeric_val(r_grpo.get(col_grpo_rate)) if col_grpo_rate else 0.0
                grpo_rate_mult = parse_numeric_val(r_grpo.get(col_grpo_doc_rate)) if col_grpo_doc_rate else 1.0
                grpo_rate_inr = grpo_price * grpo_rate_mult
                
                po_qty_sum += grpo_qty
                line_val = parse_numeric_val(r_grpo.get(col_grpo_line_total)) if col_grpo_line_total else (grpo_qty * grpo_rate_inr)
                po_val_sum += line_val
                
                if grpo_rate_inr > 0:
                    grpo_rate_str = f"{grpo_rate_inr:.2f}"
                    if grpo_rate_str not in po_rates:
                        po_rates.append(grpo_rate_str)

        if matched_grpos:
            for r_grpo in matched_grpos:
                g_no = normalize_id(r_grpo.get(col_grpo_no))
                if g_no and g_no != "—" and g_no not in unique_grns:
                    unique_grns.append(g_no)
                
                # Fetch AP Invoices matching this po_parts and g_no
                if g_no:
                    ap_list = []
                    if po_parts:
                        for p in po_parts:
                            candidates = ap_lookup.get((p, g_no))
                            if candidates:
                                ap_list.extend(candidates)
                    else:
                        candidates = ap_lookup.get(("", g_no))
                        if candidates:
                            ap_list.extend(candidates)
                            
                    if ap_list:
                        for r_ap in ap_list:
                            a_no = normalize_id(r_ap.get(col_ap_inv_no))
                            if a_no and a_no != "—" and a_no not in unique_aps:
                                unique_aps.append(a_no)
                
                if v_code_grpo == "—" and col_grpo_vendor_code:
                    v_code_grpo = clean_str_val(r_grpo.get(col_grpo_vendor_code, ""))
                if v_name_grpo == "—" and col_grpo_vendor_name:
                    v_name_grpo = clean_str_val(r_grpo.get(col_grpo_vendor_name, ""))
                if v_bill_no_grpo == "—" and col_grpo_vendor_ref:
                    v_bill_no_grpo = clean_str_val(r_grpo.get(col_grpo_vendor_ref, ""))
                if not currency and col_grpo_currency:
                    currency = str(r_grpo.get(col_grpo_currency, "")).strip()

            for r_grpo in matched_grpos:
                grpo_date_val = r_grpo.get("parsed_grpo_date")
                grpo_date = grpo_date_val if pd.notna(grpo_date_val) else None
                if grpo_date:
                    grpo_date_str = fmt_dt(grpo_date)
                    if grpo_date_str not in unique_grpo_dts:
                        unique_grpo_dts.append(grpo_date_str)
                        
                    if ge_date:
                        days_val = int((grpo_date - ge_date).days)
                        days_vals.append(str(days_val))
                        if days_val < 0:
                            is_exc = 1
                        if days_val > 3:
                            exceeds_3 = 1

            if is_exc == 1:
                ge_gt_grpo_cnt += 1
            elif days_vals:
                has_positive = any(int(d) > 0 for d in days_vals)
                if has_positive:
                    ge_lt_grpo_cnt += 1
                else:
                    ge_eq_grpo_cnt += 1
        else:
            missing_grpo_date_cnt += 1
            
        # Vendor Code/Name Fallbacks
        v_code = v_code_grpo if v_code_grpo != "—" else clean_str_val(row.get(col_ge_vendor_code, ""))
        v_name = v_name_grpo if v_name_grpo != "—" else clean_str_val(row.get(col_ge_vendor_name, ""))
        v_bill_no = v_bill_no_grpo if v_bill_no_grpo != "—" else clean_str_val(row.get(col_ge_vendor_bill_no, ""))
        
        # Fallback to PO Report for vendor details if still missing
        if (not v_code or v_code == "—") and matched_po_lines:
            for r_po in matched_po_lines:
                vc = clean_str_val(r_po.get(col_po_vendor_code, "")) if col_po_vendor_code else "—"
                if vc and vc != "—":
                    v_code = vc
                    break
        if (not v_name or v_name == "—") and matched_po_lines:
            for r_po in matched_po_lines:
                vn = clean_str_val(r_po.get(col_po_vendor_name, "")) if col_po_vendor_name else "—"
                if vn and vn != "—":
                    v_name = vn
                    break
        
        if not currency:
            if po_parts:
                currency = po_currency_lookup.get(po_parts[0], "")
        vendor_country = "India" if currency.upper() in ("INR", "") else "USA"
        
        grn_str = ", ".join(unique_grns) if unique_grns else "—"
        ap_str = ", ".join(unique_aps) if unique_aps else "—"
        grpo_dt_str = ", ".join(unique_grpo_dts) if unique_grpo_dts else "—"
        item_code_str = ", ".join(po_item_codes) if po_item_codes else "—"
        item_desc_str = ", ".join(po_item_descs) if po_item_descs else "—"
        item_group_str = ", ".join(po_item_groups) if po_item_groups else "—"
        days_str = ", ".join(days_vals) if days_vals else "—"
        rate_str = ", ".join(po_rates) if po_rates else "—"
        
        rec = {
            "Gate Entry number": ge_no,
            "Gate Entry Date": fmt_dt(ge_date),
            "PO Number": po_no if po_no else "—",
            "GRN Number": grn_str,
            "AP Invoice Number": ap_str,
            "GRPO Date": grpo_dt_str,
            "Vendor Code": v_code,
            "Vendor Name": v_name,
            "Vendor Country": vendor_country,
            "Vendor Bill Number": v_bill_no,
            "Item Code": item_code_str,
            "Item Description": item_desc_str,
            "Item Group": item_group_str,
            "Quantity": po_qty_sum,
            "Rate(INR)": rate_str,
            "Value(INR)": po_val_sum,
            "Days(GRPO-GE)": days_str,
            "Seq Exception(GE>GRPO)": is_exc,
            "Exceeds 3 days": exceeds_3
        }
        records.append(rec)
        if is_exc == 1:
            exceptions_rows.append({
                "GE No": ge_no,
                "GE Date": fmt_dt(ge_date),
                "GRPO Date": grpo_dt_str,
                "Vendor Bill Date": fmt_dt(v_bill_date),
                "Vendor Bill No": v_bill_no,
                "Vendor Code": v_code,
                "GRPO No": grn_str,
            })

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
