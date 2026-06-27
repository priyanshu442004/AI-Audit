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

def clean_str_val(val) -> str:
    if pd.isna(val) or val is None:
        return "—"
    s = str(val).strip()
    # Replace unicode replacement chars
    s = s.replace("\ufffd", "").strip()
    if s.lower() in ("nan", "none", "", "—"):
        return "—"
    return s

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
    col_doc_rate = find_col(df_po, ["document rate", "doc rate", "rate", "documentrate"])

    # Column detection GRPO
    col_grpo_po_no = None
    col_grpo_item_code = None
    col_grpo_no = None
    col_grpo_qty = None
    col_grpo_rate = None
    col_grpo_ge_no = None
    if df_grpo is not None and not df_grpo.empty:
        col_grpo_po_no = find_col(df_grpo, ["po number", "po no", "po no.", "purchase order number", "purchase order no"])
        col_grpo_item_code = find_col(df_grpo, ["item code", "item_code", "item no", "item no.", "itemno"])
        col_grpo_no = find_col(df_grpo, ["grpo no", "grpo no.", "receipt no", "grpo number", "grpono", "goods receipt no", "grn", "grn no", "grn no.", "grn number"])
        col_grpo_qty = find_col(df_grpo, ["po qty", "grpo qty", "received qty", "quantity", "qty", "received quantity"])
        col_grpo_rate = find_col(df_grpo, ["po price", "grpo rate", "unit price", "price", "rate", "item price", "unit cost"])
        col_grpo_ge_no = find_col(df_grpo, ["gate entry no", "ge no", "gate entry number", "gateentryno", "security entry no", "linked gate entry", "gate no", "entry no"])

    # Build GRPO Lookup and quantities lookup
    grpo_no_lookup = {}
    grpo_qty_lookup = {}
    grpo_rate_lookup = {}
    
    # Pre-build lookup mappings to support comma-separated PO values properly
    if df_grpo is not None and not df_grpo.empty and col_grpo_po_no and col_grpo_item_code:
        for _, row in df_grpo.iterrows():
            po_raw = row.get(col_grpo_po_no)
            item_raw = row.get(col_grpo_item_code)
            if pd.isna(po_raw) or pd.isna(item_raw):
                continue
            item_norm = normalize_id(item_raw).upper()
            if not item_norm:
                continue
            
            po_str = str(po_raw)
            po_parts = [normalize_id(p.strip()) for p in po_str.split(",") if p.strip()]
            grn = normalize_id(row.get(col_grpo_no)) if col_grpo_no else ""
            qty = parse_numeric_val(row.get(col_grpo_qty)) if col_grpo_qty else 0.0
            
            for po in po_parts:
                if not po:
                    continue
                key = (po, item_norm)
                if key not in grpo_no_lookup:
                    grpo_no_lookup[key] = []
                if grn and grn.lower() not in ("nan", "none", "") and grn not in grpo_no_lookup[key]:
                    grpo_no_lookup[key].append(grn)
                
                qty_key = (po, item_norm, grn)
                grpo_qty_lookup[qty_key] = grpo_qty_lookup.get(qty_key, 0.0) + qty
                
        # Group for average GRPO rate (as in original logic)
        for (po, item), group in df_grpo.groupby([col_grpo_po_no, col_grpo_item_code]):
            po_str = normalize_id(po)
            item_str = normalize_id(item).upper()
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

    # UOM consistent logic
    # "if a vendor have all the UOM same in all rows for particular vendor, UOM consistent column should have 1 in all rows, otherwise 0 in all rows"
    vendor_uoms_consistent = {}
    if col_vendor_code:
        for vc, group in df_po.groupby(col_vendor_code):
            vc_str = normalize_id(vc)
            if col_uom:
                uoms = group[col_uom].fillna("").astype(str).str.strip().str.upper().tolist()
                unique_uoms = set(uoms)
                # If there's an empty UOM or more than 1 unique UOM
                if "" in unique_uoms or len(unique_uoms) > 1 or len(unique_uoms) == 0:
                    vendor_uoms_consistent[vc_str] = 0
                else:
                    vendor_uoms_consistent[vc_str] = 1
            else:
                vendor_uoms_consistent[vc_str] = 0

    # count of PO numbers assigned to a vendor, and PO numbers list
    vendor_po_counts = {}
    vendor_po_list = {}
    if col_vendor_code:
        for vc, group in df_po.groupby(col_vendor_code):
            vc_str = normalize_id(vc)
            if col_po_no:
                pos = sorted(list(group[col_po_no].dropna().astype(str).str.strip().unique()))
                pos = [p for p in pos if p and p.lower() not in ("nan", "none", "")]
                vendor_po_counts[vc_str] = len(pos)
                vendor_po_list[vc_str] = ", ".join(pos) if pos else "—"
            else:
                vendor_po_counts[vc_str] = 0
                vendor_po_list[vc_str] = "—"

    # Process rows
    po_records = df_po.to_dict(orient="records")
    all_grns = set()

    # Pre-calculate line statistics
    line_data = []
    for row in po_records:
        vc = clean_str_val(row.get(col_vendor_code, "")) if col_vendor_code else "—"
        vn = clean_str_val(row.get(col_vendor_name, "")) if col_vendor_name else "—"
        
        curr = clean_str_val(row.get(col_currency, "")).upper() if col_currency else "—"
        country = "India" if curr == "INR" else "United States"
        vg = clean_str_val(row.get(col_vendor_group, "")) if col_vendor_group else "—"
        
        doc_date = clean_str_val(row.get(col_doc_date, "")) if col_doc_date else "—"
        post_date = clean_str_val(row.get(col_post_date, "")) if col_post_date else "—"
        
        ic = clean_str_val(row.get(col_item_code, "")) if col_item_code else "—"
        idesc = clean_str_val(row.get(col_item_desc, "")) if col_item_desc else "—"
        ig = clean_str_val(row.get(col_item_group, "")) if col_item_group else "—"
        uom = clean_str_val(row.get(col_uom, "")) if col_uom else "—"
        
        po_num = clean_str_val(row.get(col_po_no, "")) if col_po_no else "—"
        po_num_norm = normalize_id(row.get(col_po_no, "")) if col_po_no else ""
        ic_norm = normalize_id(row.get(col_item_code, "")).upper() if col_item_code else ""
        
        # PO Price in INR
        po_price = parse_numeric_val(row.get(col_po_price)) if col_po_price else 0.0
        doc_rate = parse_numeric_val(row.get(col_doc_rate)) if col_doc_rate else 1.0
        po_rate_inr = po_price * doc_rate
        
        po_qty = parse_numeric_val(row.get(col_po_qty)) if col_po_qty else 0.0
        
        # GRN numbers & Received qty
        grns_list = grpo_no_lookup.get((po_num_norm, ic_norm), [])
        grn_str = ", ".join(grns_list) if grns_list else "—"
        
        # Clean grn_str from any bad unicode chars
        grn_str = clean_str_val(grn_str)
        
        rec_qty = 0.0
        for g in grns_list:
            rec_qty += grpo_qty_lookup.get((po_num_norm, ic_norm, g), 0.0)
            
        # Gate Entry date
        ge_dates = ge_lookup.get(po_num_norm, [])
        ge_date_str = ", ".join(ge_dates) if ge_dates else "—"
        ge_date_str = clean_str_val(ge_date_str)
        
        line_data.append({
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
            "po_num": po_num_norm,
            "po_rate_inr": po_rate_inr,
            "po_qty": po_qty,
            "rec_qty": rec_qty,
            "grn_str": grn_str,
            "ge_date_str": ge_date_str,
            "grns_list": grns_list
        })

    # Group by (vendor_code, item_code) for Same Vendor aggregates
    agg_by_vendor_item = {}
    for item in line_data:
        key = (item["vendor_code"], item["item_code"])
        if key not in agg_by_vendor_item:
            agg_by_vendor_item[key] = {
                "prices": [],
                "ordered_qty": 0.0,
                "received_qty": 0.0
            }
        agg_by_vendor_item[key]["prices"].append(item["po_rate_inr"])
        agg_by_vendor_item[key]["ordered_qty"] += item["po_qty"]
        agg_by_vendor_item[key]["received_qty"] += item["rec_qty"]

    vendor_item_stats = {}
    for key, val in agg_by_vendor_item.items():
        prices = [p for p in val["prices"] if p > 0]
        if not prices:
            prices = val["prices"] if val["prices"] else [0.0]
        min_p = min(prices)
        max_p = max(prices)
        avg_p = sum(prices) / len(prices) if prices else 0.0
        
        spread_gt_5 = 0
        if min_p > 0 and (max_p - min_p) / min_p > 0.05:
            spread_gt_5 = 1
            
        vendor_item_stats[key] = {
            "min_price": min_p,
            "max_price": max_p,
            "avg_price": avg_p,
            "spread_gt_5": spread_gt_5,
            "ordered_qty": val["ordered_qty"],
            "received_qty": val["received_qty"]
        }

    out_rows = []
    for item in line_data:
        vc = item["vendor_code"]
        ic = item["item_code"]
        
        for g in item["grns_list"]:
            all_grns.add(g)

        if mode == "same":
            stats = vendor_item_stats.get((vc, ic), {
                "min_price": 0.0,
                "max_price": 0.0,
                "avg_price": 0.0,
                "spread_gt_5": 0,
                "ordered_qty": 0.0,
                "received_qty": 0.0
            })
            min_p = stats["min_price"]
            max_p = stats["max_price"]
            avg_p = stats["avg_price"]
            spread_gt_5 = stats["spread_gt_5"]
            ord_q = stats["ordered_qty"]
            rec_q = stats["received_qty"]
            
            uom_consistent = vendor_uoms_consistent.get(vc, 1)
            no_pos = vendor_po_counts.get(vc, 0)
            po_nums = vendor_po_list.get(vc, "—")
            
            out_rows.append({
                "vendor_code": vc if vc else "—",
                "vendor_name": item["vendor_name"],
                "vendor_country": item["vendor_country"],
                "vendor_group": item["vendor_group"],
                "document_date": item["document_date"],
                "posting_date": item["posting_date"],
                "item_code": ic if ic else "—",
                "item_description": item["item_description"],
                "item_group": item["item_group"],
                "uom": item["uom"],
                "uom_consistent": uom_consistent,
                "no_of_pos": no_pos,
                "po_numbers": po_nums,
                "ordered_qty": ord_q,
                "received_qty": rec_q,
                "min_price": min_p,
                "avg_price": avg_p,
                "max_price": max_p,
                "spread_gt_5": spread_gt_5,
                "variance_flag": spread_gt_5,
                "grn_number": item["grn_str"],
                "gate_entry_date": item["ge_date_str"]
            })
        else:
            # Cross-vendor mode: original columns preserved
            po_rate = item["po_rate_inr"]
            po_num = item["po_num"]
            grpo_rate = grpo_rate_lookup.get((po_num, ic.upper()), po_rate)
            price_variance = abs(po_rate - grpo_rate)
            variance_pct = (price_variance / po_rate * 100.0) if po_rate > 0 else 0.0
            variance_flag = 1 if variance_pct > 5.0 else 0
            
            # In cross mode: vendor uom consistency flag (from original logic)
            uom_consistent = 1
            if col_uom and col_vendor_code and col_item_code:
                # get PO rows for this vendor
                vendor_po_rows = df_po[df_po[col_vendor_code].apply(normalize_id) == vc]
                # get unique uoms for this item
                item_uoms = vendor_po_rows[vendor_po_rows[col_item_code].apply(normalize_id).str.upper() == ic.upper()][col_uom].dropna().astype(str).str.strip().unique()
                if len(item_uoms) > 1:
                    uom_consistent = 0

            out_rows.append({
                "vendor_code": vc if vc else "—",
                "vendor_name": item["vendor_name"],
                "vendor_country": item["vendor_country"],
                "vendor_group": item["vendor_group"],
                "document_date": item["document_date"],
                "posting_date": item["posting_date"],
                "item_code": ic if ic else "—",
                "item_description": item["item_description"],
                "item_group": item["item_group"],
                "uom": item["uom"],
                "uom_consistent": uom_consistent,
                "grn_number": item["grn_str"],
                "gate_entry_date": item["ge_date_str"],
                "po_rate": po_rate,
                "grpo_rate": grpo_rate,
                "price_variance": round(price_variance, 2),
                "variance_pct": round(variance_pct, 2),
                "variance_flag": variance_flag
            })

    # Group/Sort rows
    if mode == "same":
        out_rows.sort(key=lambda x: x["vendor_code"])
    else:
        out_rows.sort(key=lambda x: x["item_code"])

    # Calculate KPIs
    vendor_items = len(out_rows)
    # Count of vendors with inconsistent UOM
    if mode == "same":
        uom_inconsistent_count = sum(1 for vc, inc in vendor_uoms_consistent.items() if inc == 0)
    else:
        # Cross vendor uom inconsistency
        inconsistent_vendors = set()
        for r in out_rows:
            if r["uom_consistent"] == 0:
                inconsistent_vendors.add(r["vendor_code"])
        uom_inconsistent_count = len(inconsistent_vendors)

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
