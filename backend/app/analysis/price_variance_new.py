from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime

def find_col(df: pd.DataFrame, aliases: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    aliases_set = {a.lower().strip() for a in aliases}
    for col in df.columns:
        if str(col).lower().strip() in aliases_set:
            return col
    return None

def normalize_id(val) -> str:
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def parse_numeric_val(val) -> float:
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except:
        return 0.0

def run_variance_analysis(dfs: dict[str, pd.DataFrame], mode: str) -> dict:
    """
    mode: 'same' or 'cross'
    """
    df_po = dfs.get("purchase_order")
    if df_po is None or df_po.empty:
        return {"rows": [], "kpis": {"vendor_items": 0, "uom_inconsistent": 0, "unique_grn_nos": 0, "variance_lines": 0}}

    df_grpo = dfs.get("grpo")
    df_ge = dfs.get("gate_entry")

    # Column detection PO
    col_po_no = find_col(df_po, ["po no", "po no.", "po number", "purchase order no", "purchase order number"])
    col_doc_date = find_col(df_po, ["document date", "doc date", "documentdate"])
    col_post_date = find_col(df_po, ["posting date", "post date", "postingdate", "po date", "po_date"])
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

    # Column detection GRPO
    col_grpo_po_no = None
    col_grpo_item_code = None
    col_grpo_no = None
    col_grpo_rate = None
    if df_grpo is not None and not df_grpo.empty:
        col_grpo_po_no = find_col(df_grpo, ["po number", "po no", "po no.", "purchase order number", "purchase order no"])
        col_grpo_item_code = find_col(df_grpo, ["item code", "item_code", "item no", "item no.", "itemno"])
        col_grpo_no = find_col(df_grpo, ["grpo no", "grpo no.", "receipt no", "grpo number", "grpono", "goods receipt no", "grn", "grn no", "grn no.", "grn number"])
        col_grpo_rate = find_col(df_grpo, ["po price", "grpo rate", "unit price", "price", "rate", "item price", "unit cost"])

    # Build GRPO Lookup
    grpo_no_lookup = {}
    grpo_rate_lookup = {}
    if df_grpo is not None and not df_grpo.empty and col_grpo_po_no and col_grpo_item_code:
        for (po, item), group in df_grpo.groupby([col_grpo_po_no, col_grpo_item_code]):
            po_str = normalize_id(po)
            item_str = normalize_id(item).upper()
            
            # GRN numbers
            if col_grpo_no:
                grns = list(group[col_grpo_no].dropna().apply(normalize_id).unique())
                grns = [g for g in grns if g and g.lower() not in ("nan", "none", "")]
            else:
                grns = []
            grpo_no_lookup[(po_str, item_str)] = grns

            # GRPO Rate (average of non-zero rates)
            if col_grpo_rate:
                rates = group[col_grpo_rate].apply(parse_numeric_val)
                valid_rates = rates[rates > 0]
                if not valid_rates.empty:
                    grpo_rate_lookup[(po_str, item_str)] = valid_rates.mean()

    # Build Gate Entry Lookup
    ge_lookup = {}
    if df_ge is not None and not df_ge.empty:
        col_ge_po_no = find_col(df_ge, ["purchase order number", "purchase order no", "po number", "po no", "po no."])
        col_ge_date = find_col(df_ge, ["gate entry date", "ge date", "date"])
        if col_ge_po_no and col_ge_date:
            for po, group in df_ge.groupby(col_ge_po_no):
                po_str = normalize_id(po)
                dates = list(group[col_ge_date].dropna().astype(str).str.strip().unique())
                dates = [d for d in dates if d and d.lower() not in ["nan", "none", ""]]
                ge_lookup[po_str] = dates

    # Vendor level UOM consistency check:
    # "if a vendor has multiple UOM for same item code, or if UOM is blank or different across rows for same item code and vendor then we will flag it"
    vendor_uoms_inconsistent = {}
    if col_vendor_code and col_item_code:
        for vc, group in df_po.groupby(col_vendor_code):
            vc_str = normalize_id(vc)
            is_inconsistent = 0
            # group by item code
            for ic, item_group in group.groupby(col_item_code):
                if col_uom:
                    uoms_series = item_group[col_uom].astype(str).str.strip()
                    # Clean UOM list
                    uoms_list = [u for u in uoms_series if u and u.lower() not in ("nan", "none")]
                    # If count of non-empty UOMs is less than group length (means blank exists), or if >1 unique UOM
                    if len(uoms_list) < len(item_group) or len(set(uoms_list)) > 1:
                        is_inconsistent = 1
                        break
                else:
                    is_inconsistent = 1
                    break
            vendor_uoms_inconsistent[vc_str] = is_inconsistent

    # Process rows
    po_records = df_po.to_dict(orient="records")
    out_rows = []
    all_grns = set()

    for idx, row in enumerate(po_records):
        vc = normalize_id(row.get(col_vendor_code, "")) if col_vendor_code else ""
        vn = str(row.get(col_vendor_name, "")).strip() if col_vendor_name else ""
        
        # Vendor Country based on currency
        curr = str(row.get(col_currency, "")).strip().upper() if col_currency else ""
        country = "India" if curr == "INR" else "United States"

        vg = str(row.get(col_vendor_group, "")).strip() if col_vendor_group else ""
        doc_date = str(row.get(col_doc_date, "")).strip() if col_doc_date else ""
        post_date = str(row.get(col_post_date, "")).strip() if col_post_date else ""
        ic = normalize_id(row.get(col_item_code, "")) if col_item_code else ""
        idesc = str(row.get(col_item_desc, "")).strip() if col_item_desc else ""
        ig = str(row.get(col_item_group, "")).strip() if col_item_group else ""
        uom = str(row.get(col_uom, "")).strip() if col_uom else ""

        po_num = normalize_id(row.get(col_po_no, "")) if col_po_no else ""

        # GRN Numbers
        grns_list = grpo_no_lookup.get((po_num, ic.upper()), [])
        grn_str = ", ".join(grns_list) if grns_list else "—"
        for g in grns_list:
            all_grns.add(g)

        # Gate Entry Date
        ge_dates = ge_lookup.get(po_num, [])
        ge_date_str = ", ".join(ge_dates) if ge_dates else "—"

        po_rate = parse_numeric_val(row.get(col_po_price, 0.0)) if col_po_price else 0.0
        grpo_rate = grpo_rate_lookup.get((po_num, ic.upper()), po_rate)

        price_variance = abs(po_rate - grpo_rate)
        variance_pct = (price_variance / po_rate * 100.0) if po_rate > 0 else 0.0
        variance_flag = 1 if variance_pct > 5.0 else 0

        uom_consistent = 0 if vendor_uoms_inconsistent.get(vc, 0) == 1 else 1

        out_rows.append({
            "vendor_code": vc,
            "vendor_name": vn,
            "vendor_country": country,
            "vendor_group": vg,
            "document_date": doc_date,
            "posting_date": post_date,
            "item_code": ic,
            "item_description": idesc,
            "item_group": ig,
            "uom": uom,
            "uom_consistent": uom_consistent,
            "grn_number": grn_str,
            "gate_entry_date": ge_date_str,
            "po_rate": po_rate,
            "grpo_rate": grpo_rate,
            "price_variance": round(price_variance, 2),
            "variance_pct": round(variance_pct, 2),
            "variance_flag": variance_flag
        })

    # Group/Sort rows
    if mode == "same":
        # Group/Sort by vendor code first
        out_rows.sort(key=lambda x: x["vendor_code"])
    else:
        # Group/Sort by item code first
        out_rows.sort(key=lambda x: x["item_code"])

    # Calculate KPIs
    vendor_items = len(out_rows)
    uom_inconsistent_count = sum(1 for vc, inc in vendor_uoms_inconsistent.items() if inc == 1)
    unique_grn_nos = len(all_grns)
    variance_lines = sum(1 for r in out_rows if r["variance_flag"] == 1)

    return {
        "rows": out_rows,
        "kpis": {
            "vendor_items": vendor_items,
            "uom_inconsistent": uom_inconsistent_count,
            "unique_grn_nos": unique_grn_nos,
            "variance_lines": variance_lines
        }
    }
