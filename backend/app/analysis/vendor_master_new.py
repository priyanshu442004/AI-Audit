from __future__ import annotations
import pandas as pd
import numpy as np

def is_nan_or_none(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and val != val:  # Fast NaN check
        return True
    return False

def normalize_id(val) -> str:
    if is_nan_or_none(val):
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def run_vendor_master_new(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Computes Vendor Master analytics page data.
    Filters BP Master to only include vendor codes starting with 'V'.
    Reconciles with PO Report for unique PO count KPI.
    """
    df_bp = dfs.get("vendor_master")
    df_po = dfs.get("purchase_order")

    out_rows = []
    kpis = {
        "total_suppliers": 0,
        "same_gstin_multi_codes": 0,
        "missing_gstin_domestic": 0,
        "missing_gstin_foreign": 0,
        "dormant_vendors": 0,
        "unique_po_numbers": 0,
    }

    # 1. Calculate unique PO numbers KPI
    if df_po is not None and not df_po.empty:
        col_po_no = None
        for col in df_po.columns:
            if str(col).lower().strip() in ("po no", "po_no", "po number", "purchase order number"):
                col_po_no = col
                break
        if col_po_no:
            po_series = df_po[col_po_no].dropna().astype(str).str.strip()
            po_series = po_series[po_series != ""]
            kpis["unique_po_numbers"] = int(po_series.nunique())

    if df_bp is None or df_bp.empty:
        return {
            "rows": [],
            "kpis": kpis
        }

    # 2. Extract column mappings from BP Master
    col_bp_code = None
    col_bp_name = None
    col_currency = None
    col_group_name = None
    col_gstin = None
    col_msme = None
    col_payment_terms = None
    col_active = None

    for col in df_bp.columns:
        col_lower = str(col).lower().strip()
        if col_lower in ("bp code", "bp_code", "card code", "cardcode", "code"):
            col_bp_code = col
        elif col_lower in ("bp name", "bp_name", "card name", "cardname", "name"):
            col_bp_name = col
        elif col_lower in ("bp currency", "bp_currency", "currency", "doc currency", "currency code"):
            col_currency = col
        elif col_lower in ("group name", "group_name", "vendor group", "vendor_group"):
            col_group_name = col
        elif col_lower in ("gstin", "gstin number", "gstin_no", "tax id"):
            col_gstin = col
        elif col_lower in ("msme registration", "msme_registration", "msme registeration", "msme category"):
            col_msme = col
        elif col_lower in ("payment terms code", "payment terms", "terms code", "payment_terms"):
            col_payment_terms = col
        elif col_lower in ("active", "status", "bp status"):
            col_active = col

    # Fallbacks if some columns are not automatically matched
    col_bp_code = col_bp_code or "BP Code"
    col_bp_name = col_bp_name or "BP Name"
    col_currency = col_currency or "BP Currency"
    col_group_name = col_group_name or "Group Name"
    col_gstin = col_gstin or "GSTIN"
    col_msme = col_msme or "MSME Registration"
    col_payment_terms = col_payment_terms or "Payment Terms Code"
    col_active = col_active or "Active"

    # 3. Filter vendors where vendor code starts with V (case-insensitive)
    valid_rows = []
    for _, row in df_bp.iterrows():
        code_raw = row.get(col_bp_code)
        if is_nan_or_none(code_raw):
            continue
        code = str(code_raw).strip()
        if not code.upper().startswith("V"):
            continue
        valid_rows.append(row)

    if not valid_rows:
        return {
            "rows": [],
            "kpis": kpis
        }

    # Re-build a clean dataframe of valid vendors
    df_valid = pd.DataFrame(valid_rows)

    # 4. Compute GSTIN counts to determine same_gst_multi_code
    # Helper to clean GSTIN value
    def clean_gstin(val) -> str:
        if is_nan_or_none(val):
            return ""
        val_str = str(val).strip()
        if val_str.lower() in ("nan", "none", "", "—"):
            return ""
        return val_str.upper()

    df_valid["clean_gst"] = df_valid[col_gstin].apply(clean_gstin)
    
    # Exclude empty GSTINs when computing duplicates
    gst_counts = df_valid[df_valid["clean_gst"] != ""]["clean_gst"].value_counts().to_dict()

    # Related parties list
    RELATED_PARTIES = {
        "ROYALUX LIGHTING PVT LTD",
        "IKIO SOLUTIONS PRIVATE LIMITED(UNIT-2)",
        "IKIO SOLUTIONS PVT LTD",
        "ROYALUX LIGHTING PRIVATE LIMITED- UNIT -2"
    }

    # 5. Process each row
    for _, row in df_valid.iterrows():
        code = str(row.get(col_bp_code)).strip()
        name = str(row.get(col_bp_name, "—")).strip() if not is_nan_or_none(row.get(col_bp_name)) else "—"
        
        # Currency & Country
        curr = str(row.get(col_currency, "—")).strip() if not is_nan_or_none(row.get(col_currency)) else "—"
        curr_upper = curr.upper()
        country = "India" if curr_upper == "INR" else "USA"
        
        # Region
        region = "Domestic" if country == "India" else "Foreign"
        
        # Vendor Group
        group = str(row.get(col_group_name, "—")).strip() if not is_nan_or_none(row.get(col_group_name)) else "—"
        
        # GSTIN & MSME
        gst = str(row.get(col_gstin, "—")).strip() if not is_nan_or_none(row.get(col_gstin)) else "—"
        msme = str(row.get(col_msme, "—")).strip() if not is_nan_or_none(row.get(col_msme)) else "—"
        
        # Payment Terms & Active Status
        pay_terms = str(row.get(col_payment_terms, "—")).strip() if not is_nan_or_none(row.get(col_payment_terms)) else "—"
        
        act_raw = str(row.get(col_active, "")).strip().upper()
        active_status = "Active" if act_raw == "Y" else "Dormant"
        
        # Calculations: same_gst_multi_code
        clean_gst_val = clean_gstin(row.get(col_gstin))
        same_gst_multi_code = 0
        if clean_gst_val != "" and gst_counts.get(clean_gst_val, 0) > 1:
            same_gst_multi_code = 1
            
        # Missing GSTIN logic
        # "Missing GSTIN"-> if the vendor is domestic and don't have GSTIN Number then 1 otherwise 0
        is_gstin_empty = (clean_gst_val == "")
        missing_gstin = 1 if (region == "Domestic" and is_gstin_empty) else 0
        
        # Foreign w/ GSTIN logic
        # "Foreign w/ GSTIN"-> if the vendor is foreign and don't have GSTIN Number then 1 otherwise 0
        foreign_w_gstin = 1 if (region == "Foreign" and is_gstin_empty) else 0
        
        # Related Party check
        related_party = 1 if name.upper() in RELATED_PARTIES else 0

        out_rows.append({
            "vendor_code": code,
            "vendor_name": name,
            "vendor_country": country,
            "vendor_group": group,
            "region": region,
            "currency": curr,
            "gstin": gst,
            "msme_registration": msme,
            "payment_terms": pay_terms,
            "active": active_status,
            "same_gst_multi_code": same_gst_multi_code,
            "missing_gstin": missing_gstin,
            "foreign_w_gstin": foreign_w_gstin,
            "related_party": related_party
        })

    # Sort rows by vendor_code
    out_rows.sort(key=lambda x: x["vendor_code"])

    # 6. Calculate KPIs from resultant table
    total_suppliers = len(out_rows)
    
    # same_gstin_multi_codes is the count of UNIQUE GSTINs registered under multiple vendors
    same_gstin_multi_codes_count = sum(1 for count in gst_counts.values() if count > 1)
    
    missing_gstin_domestic = sum(r["missing_gstin"] for r in out_rows)
    missing_gstin_foreign = sum(r["foreign_w_gstin"] for r in out_rows)
    dormant_vendors = sum(1 for r in out_rows if r["active"] == "Dormant")

    kpis["total_suppliers"] = total_suppliers
    kpis["same_gstin_multi_codes"] = same_gstin_multi_codes_count
    kpis["missing_gstin_domestic"] = missing_gstin_domestic
    kpis["missing_gstin_foreign"] = missing_gstin_foreign
    kpis["dormant_vendors"] = dormant_vendors

    return {
        "rows": out_rows,
        "kpis": kpis
    }
