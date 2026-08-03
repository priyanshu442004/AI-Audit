from __future__ import annotations
import pandas as pd
import numpy as np

def is_nan_or_none(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and val != val:  # Fast NaN check
        return True
    s = str(val).strip().lower()
    if s in ("nan", "none", "null", "nat", ""):
        return True
    return False

def normalize_id(val) -> str:
    if is_nan_or_none(val):
        return ""
    val_str = str(val).strip().replace('"', '').replace("'", "")
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def parse_num(v) -> float:
    if is_nan_or_none(v):
        return 0.0
    s = str(v).replace(",", "").replace("₹", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def find_col(df: pd.DataFrame, options: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    normalized_options = {o.lower().replace(" ", "").replace("_", "").replace(".", ""): o for o in options}
    for col in df.columns:
        norm_col = str(col).lower().replace(" ", "").replace("_", "").replace(".", "")
        if norm_col in normalized_options:
            return col
    # Partial match fallback
    for col in df.columns:
        norm_col = str(col).lower().replace(" ", "").replace("_", "").replace(".", "")
        for opt_key in normalized_options:
            if opt_key in norm_col or norm_col in opt_key:
                return col
    return None

def safe_get(row, col_name: str | None, default: str = "") -> str:
    if not col_name or col_name not in row:
        return default
    val = row[col_name]
    if is_nan_or_none(val):
        return default
    return str(val).strip()

def run_three_way_matching(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Computes 3-Way Matching analysis page data by combining:
    - AP Invoice Report / Purchase Register (base)
    - GRPO Report
    - Purchase Order Report
    - Gate Entry Report
    - AP Credit Note Report
    """
    df_ap_invoice = dfs.get("ap_invoice_report")
    if df_ap_invoice is None or df_ap_invoice.empty:
        df_ap_invoice = dfs.get("purchase_register")

    df_grpo = dfs.get("grpo")
    df_po = dfs.get("purchase_order")
    df_gate_entry = dfs.get("gate_entry")
    df_credit_note = dfs.get("ap_credit_note")

    kpis = {
        "total_grpo_lines": 0,
        "perfect_match_qty": 0.0,
        "unique_po_numbers": 0,
        "unique_grpo_numbers": 0,
        "unique_credit_notes": 0,
        "unique_po_flagged": 0,
        "unique_grn_flagged": 0,
    }

    # 1. Column lookups for GRPO Report
    grpo_dates = {}
    grpo_lines = {}
    if df_grpo is not None and not df_grpo.empty:
        col_grpo_no = find_col(df_grpo, ["GRPO No", "GRPO Number", "GRN Number", "GRN No", "Goods Receipt No", "DocNum"])
        col_grpo_item = find_col(df_grpo, ["Item Code", "Item No", "Item No.", "Part No"])
        col_grpo_posting_date = find_col(df_grpo, ["Posting Date", "Document Date", "Date", "GRPO Date", "GRN Date"])
        col_grpo_qty = find_col(df_grpo, ["PO Qty", "PO Quantity", "Qty", "Quantity", "Received Qty", "GRPO Qty"])
        col_grpo_price = find_col(df_grpo, ["PO Price", "PO Rate", "Price", "Rate", "Received Price", "GRPO Rate"])

        df_grpo = df_grpo.copy()
        df_grpo["clean_grpo_no"] = df_grpo[col_grpo_no].apply(normalize_id) if col_grpo_no in df_grpo.columns else ""
        df_grpo["clean_item_code"] = df_grpo[col_grpo_item].apply(normalize_id) if col_grpo_item in df_grpo.columns else ""

        if col_grpo_no in df_grpo.columns and col_grpo_posting_date in df_grpo.columns:
            grpo_dates = df_grpo[df_grpo["clean_grpo_no"] != ""].drop_duplicates(subset=["clean_grpo_no"]).set_index("clean_grpo_no")[col_grpo_posting_date].to_dict()

        for _, row in df_grpo.iterrows():
            clean_g_no = safe_get(row, "clean_grpo_no")
            clean_i_code = safe_get(row, "clean_item_code")
            if clean_g_no:
                k = (clean_g_no, clean_i_code)
                if k not in grpo_lines:
                    grpo_lines[k] = {
                        "qty": parse_num(row.get(col_grpo_qty)) if col_grpo_qty else 0.0,
                        "price": parse_num(row.get(col_grpo_price)) if col_grpo_price else 0.0
                    }

    # 2. Column lookups for Purchase Order Report
    po_dates = {}
    po_lines = {}
    if df_po is not None and not df_po.empty:
        col_po_no = find_col(df_po, ["PO No", "PO Number", "Purchase Order No", "Purchase Order Number", "DocNum"])
        col_po_item = find_col(df_po, ["Item Code", "Item No", "Item No.", "Part No"])
        col_po_posting_date = find_col(df_po, ["Posting Date", "Document Date", "Date", "PO Date"])
        col_po_vendor_code = find_col(df_po, ["Vendor Code", "BP Code", "Supplier Code"])
        col_po_vendor_name = find_col(df_po, ["Vendor Name", "BP Name", "Supplier Name"])
        col_po_currency = find_col(df_po, ["Document Currency", "BP Currency", "Currency"])
        col_po_item_desc = find_col(df_po, ["Item Description", "Description"])
        col_po_item_group = find_col(df_po, ["Item Group", "Group"])
        col_po_qty = find_col(df_po, ["PO Qty", "PO Quantity", "Qty", "Quantity"])
        col_po_price = find_col(df_po, ["PO Price", "PO Rate", "Price", "Rate", "Unit Price"])

        df_po = df_po.copy()
        df_po["clean_po_no"] = df_po[col_po_no].apply(normalize_id) if col_po_no in df_po.columns else ""
        df_po["clean_item_code"] = df_po[col_po_item].apply(normalize_id) if col_po_item in df_po.columns else ""

        if col_po_no in df_po.columns and col_po_posting_date in df_po.columns:
            po_dates = df_po[df_po["clean_po_no"] != ""].drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_po_posting_date].to_dict()

        for _, row in df_po.iterrows():
            clean_p_no = safe_get(row, "clean_po_no")
            clean_i_code = safe_get(row, "clean_item_code")
            if clean_p_no:
                k = (clean_p_no, clean_i_code)
                if k not in po_lines:
                    po_lines[k] = {
                        "vendor_code": safe_get(row, col_po_vendor_code),
                        "vendor_name": safe_get(row, col_po_vendor_name),
                        "currency": safe_get(row, col_po_currency).upper(),
                        "item_desc": safe_get(row, col_po_item_desc),
                        "item_group": safe_get(row, col_po_item_group),
                        "qty": parse_num(row.get(col_po_qty)) if col_po_qty else 0.0,
                        "price": parse_num(row.get(col_po_price)) if col_po_price else 0.0
                    }

    # 3. Column lookups for Gate Entry Report
    gate_entry_dates = {}
    if df_gate_entry is not None and not df_gate_entry.empty:
        col_ge_po = find_col(df_gate_entry, ["Purchase Order Number", "Purchase Order No", "PO Number", "PO No"])
        col_ge_date = find_col(df_gate_entry, ["Gate Entry Date", "GE Date", "Date"])

        if col_ge_po in df_gate_entry.columns and col_ge_date in df_gate_entry.columns:
            df_ge = df_gate_entry.copy()
            df_ge["clean_po_no"] = df_ge[col_ge_po].apply(normalize_id)
            gate_entry_dates = df_ge[df_ge["clean_po_no"] != ""].drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_ge_date].to_dict()

    # 4. Column lookups for AP Credit Note
    credit_notes = {}
    if df_credit_note is not None and not df_credit_note.empty:
        col_cn_ap_no = find_col(df_credit_note, ["AP Invoice Number", "AP Invoice No", "Invoice No", "Invoice Number"])
        col_cn_no = find_col(df_credit_note, ["AP Credit Note No", "AP Credit Note Number", "Credit Note No", "DocNum"])

        if col_cn_ap_no in df_credit_note.columns and col_cn_no in df_credit_note.columns:
            df_cn = df_credit_note.copy()
            df_cn["clean_ap_invoice_no"] = df_cn[col_cn_ap_no].apply(normalize_id)
            credit_notes = df_cn[df_cn["clean_ap_invoice_no"] != ""].drop_duplicates(subset=["clean_ap_invoice_no"]).set_index("clean_ap_invoice_no")[col_cn_no].to_dict()

    # Process base lines (either AP Invoice or GRPO)
    df_base = None
    col_ap_grpo_no = None
    col_ap_po_no = None
    col_ap_invoice_no = None
    col_ap_item_code = None
    col_ap_posting_date = None
    col_ap_qty = None
    col_ap_price = None
    col_ap_item_desc = None
    col_ap_item_group = None
    col_ap_vendor_code = None
    col_ap_vendor_name = None
    col_ap_currency = None

    if df_ap_invoice is not None and not df_ap_invoice.empty:
        col_ap_grpo_no = find_col(df_ap_invoice, ["GRPO Number", "GRPO No", "GRN Number", "GRN No", "Base Ref", "Base Ref.", "Linked GRPO", "Base Doc"])
        col_ap_po_no = find_col(df_ap_invoice, ["PO Number", "PO No", "Purchase Order Number", "Order No", "Base PO"])
        col_ap_invoice_no = find_col(df_ap_invoice, ["AP Invoice No", "AP Invoice Number", "Invoice No", "Invoice Number", "Document No", "DocNo", "DocNum"])
        col_ap_item_code = find_col(df_ap_invoice, ["Item Code", "Item No", "Item No.", "Part No"])
        col_ap_posting_date = find_col(df_ap_invoice, ["Posting Date", "Document Date", "Date", "Invoice Date"])
        col_ap_qty = find_col(df_ap_invoice, ["Invoice Qty", "Invoice Quantity", "Quantity", "Qty"])
        col_ap_price = find_col(df_ap_invoice, ["Invoice Price", "Invoice Rate", "Price", "Rate", "Unit Price"])
        col_ap_item_desc = find_col(df_ap_invoice, ["Item Description", "Description"])
        col_ap_item_group = find_col(df_ap_invoice, ["Item Group", "Group"])
        col_ap_vendor_code = find_col(df_ap_invoice, ["Vendor Code", "BP Code", "Supplier Code"])
        col_ap_vendor_name = find_col(df_ap_invoice, ["Vendor Name", "BP Name", "Supplier Name"])
        col_ap_currency = find_col(df_ap_invoice, ["Document Currency", "BP Currency", "Currency"])

        df_ap_invoice = df_ap_invoice.copy()
        df_ap_invoice["clean_grpo_no"] = df_ap_invoice[col_ap_grpo_no].apply(normalize_id) if col_ap_grpo_no in df_ap_invoice.columns else ""
        df_ap_invoice["clean_po_no"] = df_ap_invoice[col_ap_po_no].apply(normalize_id) if col_ap_po_no in df_ap_invoice.columns else ""
        df_ap_invoice["clean_ap_invoice_no"] = df_ap_invoice[col_ap_invoice_no].apply(normalize_id) if col_ap_invoice_no in df_ap_invoice.columns else ""
        df_ap_invoice["clean_item_code"] = df_ap_invoice[col_ap_item_code].apply(normalize_id) if col_ap_item_code in df_ap_invoice.columns else ""

        df_base = df_ap_invoice[df_ap_invoice["clean_grpo_no"] != ""].copy()
        if df_base.empty:
            df_base = df_ap_invoice.copy()

    # Fallback to GRPO dataframe if df_base is still empty or None
    if (df_base is None or df_base.empty) and df_grpo is not None and not df_grpo.empty:
        col_ap_grpo_no = find_col(df_grpo, ["GRPO No", "GRPO Number", "GRN Number", "GRN No"])
        col_ap_po_no = find_col(df_grpo, ["PO Number", "PO No", "Base PO"])
        col_ap_item_code = find_col(df_grpo, ["Item Code", "Item No"])
        col_ap_qty = find_col(df_grpo, ["PO Qty", "Qty", "Quantity"])
        col_ap_price = find_col(df_grpo, ["PO Price", "Rate", "Price"])

        df_base = df_grpo.copy()
        df_base["clean_grpo_no"] = df_base[col_ap_grpo_no].apply(normalize_id) if col_ap_grpo_no in df_base.columns else ""
        df_base["clean_po_no"] = df_base[col_ap_po_no].apply(normalize_id) if col_ap_po_no in df_base.columns else ""
        df_base["clean_ap_invoice_no"] = ""
        df_base["clean_item_code"] = df_base[col_ap_item_code].apply(normalize_id) if col_ap_item_code in df_base.columns else ""

    if df_base is None or df_base.empty:
        return {
            "rows": [],
            "kpis": kpis
        }

    # Invoice Date mapping
    ap_invoice_dates = {}
    if col_ap_po_no and col_ap_posting_date and col_ap_po_no in df_base.columns and col_ap_posting_date in df_base.columns:
        ap_invoice_dates = df_base[df_base["clean_po_no"] != ""].drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_ap_posting_date].to_dict()

    out_rows = []
    unique_po_set = set()
    unique_grn_set = set()
    unique_cn_set = set()
    unique_po_flagged_set = set()
    unique_grn_flagged_set = set()
    perfect_qty_sum = 0.0

    for _, row in df_base.iterrows():
        clean_po = safe_get(row, "clean_po_no")
        clean_grpo = safe_get(row, "clean_grpo_no")
        clean_item = safe_get(row, "clean_item_code")
        clean_ap = safe_get(row, "clean_ap_invoice_no")

        # PO & GRPO matches
        po_info = po_lines.get((clean_po, clean_item))
        grpo_info = grpo_lines.get((clean_grpo, clean_item))

        # Vendor and Country details (with fallback to AP Invoice report)
        vendor_code = po_info["vendor_code"] if po_info else safe_get(row, col_ap_vendor_code)
        vendor_name = po_info["vendor_name"] if po_info else safe_get(row, col_ap_vendor_name)
        currency = po_info["currency"] if po_info else safe_get(row, col_ap_currency).upper()
        
        vendor_country = ""
        if currency:
            vendor_country = "India" if currency == "INR" else "USA"

        # Item info
        item_code = safe_get(row, col_ap_item_code)
        item_desc = po_info["item_desc"] if po_info else safe_get(row, col_ap_item_desc)
        item_group = po_info["item_group"] if po_info else safe_get(row, col_ap_item_group)

        # Quantities
        po_qty = po_info["qty"] if po_info else 0.0
        grpo_qty = grpo_info["qty"] if grpo_info else 0.0
        inv_qty = parse_num(row.get(col_ap_qty)) if col_ap_qty else 0.0

        qty_po_gt_grpo = 1 if po_qty > grpo_qty else 0
        qty_grpo_gt_inv = 1 if grpo_qty > inv_qty else 0

        # Rates
        po_rate = po_info["price"] if po_info else 0.0
        grpo_rate = grpo_info["price"] if grpo_info else 0.0
        inv_rate = parse_num(row.get(col_ap_price)) if col_ap_price else 0.0

        # Excess over 5% pricing discrepancy flag
        excess_over_5 = 0
        if grpo_rate > 0:
            if inv_rate > 1.05 * grpo_rate:
                excess_over_5 = 1
        elif inv_rate > 0:
            excess_over_5 = 1

        # Match Status
        if abs(po_qty - grpo_qty) < 1e-4 and abs(grpo_qty - inv_qty) < 1e-4:
            match_status = "Perfect match"
            perfect_qty_sum += inv_qty
        else:
            match_status = "Variance"

        # Credit Note lookup
        credit_note_val = credit_notes.get(clean_ap, "")
        credit_note_str = str(credit_note_val) if credit_note_val else ""

        # Tracking sets
        if clean_po:
            unique_po_set.add(clean_po)
            if excess_over_5 == 1:
                unique_po_flagged_set.add(clean_po)
        if clean_grpo:
            unique_grn_set.add(clean_grpo)
            if excess_over_5 == 1:
                unique_grn_flagged_set.add(clean_grpo)
        if credit_note_str:
            unique_cn_set.add(credit_note_str)

        # Dates lookup
        grpo_date_val = grpo_dates.get(clean_grpo, "")
        po_date_val = po_dates.get(clean_po, "")
        gate_entry_date_val = gate_entry_dates.get(clean_po, "")
        invoice_date_val = ap_invoice_dates.get(clean_po, "")

        out_rows.append({
            "grn_number": safe_get(row, col_ap_grpo_no, default=clean_grpo),
            "grpo_date": str(grpo_date_val) if not is_nan_or_none(grpo_date_val) else "",
            "po_number": safe_get(row, col_ap_po_no, default=clean_po),
            "po_date": str(po_date_val) if not is_nan_or_none(po_date_val) else "",
            "gate_entry_date": str(gate_entry_date_val) if not is_nan_or_none(gate_entry_date_val) else "",
            "invoice_date": str(invoice_date_val) if not is_nan_or_none(invoice_date_val) else "",
            "ap_invoice_number": safe_get(row, col_ap_invoice_no, default=clean_ap),
            "ap_credit_note": credit_note_str,
            "vendor_code": vendor_code,
            "vendor_name": vendor_name,
            "vendor_country": vendor_country,
            "item_code": item_code if item_code else clean_item,
            "item_description": item_desc,
            "item_group": item_group,
            "po_qty": po_qty,
            "grpo_qty": grpo_qty,
            "inv_qty": inv_qty,
            "qty_po_gt_grpo": qty_po_gt_grpo,
            "qty_grpo_gt_inv": qty_grpo_gt_inv,
            "po_rate": po_rate,
            "grpo_rate": grpo_rate,
            "inv_rate": inv_rate,
            "excess_over_5": excess_over_5,
            "match_status": match_status
        })

    out_rows.sort(key=lambda x: (str(x["grn_number"]), str(x["item_code"])))

    kpis["total_grpo_lines"] = len(out_rows)
    kpis["perfect_match_qty"] = perfect_qty_sum
    kpis["unique_po_numbers"] = len(unique_po_set)
    kpis["unique_grpo_numbers"] = len(unique_grn_set)
    kpis["unique_credit_notes"] = len(unique_cn_set)
    kpis["unique_po_flagged"] = len(unique_po_flagged_set)
    kpis["unique_grn_flagged"] = len(unique_grn_flagged_set)

    return {
        "rows": out_rows,
        "kpis": kpis
    }
