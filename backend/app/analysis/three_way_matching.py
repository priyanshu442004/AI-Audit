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
    normalized_options = {o.lower().replace(" ", "").replace("_", ""): o for o in options}
    for col in df.columns:
        norm_col = str(col).lower().replace(" ", "").replace("_", "").rstrip(".")
        if norm_col in normalized_options:
            return col
    return None

def run_three_way_matching(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Computes 3-Way Matching analysis page data by combining:
    - AP Invoice Report (base)
    - GRPO Report
    - Purchase Order Report
    - Gate Entry Report
    - AP Credit Note Report
    """
    df_ap_invoice = dfs.get("ap_invoice_report")
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

    if df_ap_invoice is None or df_ap_invoice.empty:
        return {
            "rows": [],
            "kpis": kpis
        }

    # 1. Column lookups for AP Invoice Report
    col_ap_grpo_no = find_col(df_ap_invoice, ["GRPO Number", "GRPO No", "GRN Number", "GRN No"]) or "GRPO Number"
    col_ap_po_no = find_col(df_ap_invoice, ["PO Number", "PO No", "Purchase Order Number"]) or "PO Number"
    col_ap_invoice_no = find_col(df_ap_invoice, ["AP Invoice No", "AP Invoice Number", "Invoice No", "Invoice Number"]) or "AP Invoice No"
    col_ap_item_code = find_col(df_ap_invoice, ["Item Code", "Item No", "Item No."]) or "Item Code"
    col_ap_posting_date = find_col(df_ap_invoice, ["Posting Date", "Document Date", "Date", "Invoice Date"]) or "Posting Date"
    col_ap_qty = find_col(df_ap_invoice, ["Invoice Qty", "Invoice Quantity", "Quantity", "Qty"]) or "Invoice Qty"
    col_ap_price = find_col(df_ap_invoice, ["Invoice Price", "Invoice Rate", "Price", "Rate"]) or "Invoice Price"
    col_ap_item_desc = find_col(df_ap_invoice, ["Item Description", "Description"]) or "Item Description"
    col_ap_item_group = find_col(df_ap_invoice, ["Item Group", "Group"]) or "Item Group"
    col_ap_vendor_code = find_col(df_ap_invoice, ["Vendor Code", "BP Code"]) or "Vendor Code"
    col_ap_vendor_name = find_col(df_ap_invoice, ["Vendor Name", "BP Name"]) or "Vendor Name"
    col_ap_currency = find_col(df_ap_invoice, ["Document Currency", "BP Currency", "Currency"]) or "Document Currency"

    # Pre-clean AP Invoice report base
    df_ap_invoice = df_ap_invoice.copy()
    df_ap_invoice["clean_grpo_no"] = df_ap_invoice[col_ap_grpo_no].apply(normalize_id)
    df_ap_invoice["clean_po_no"] = df_ap_invoice[col_ap_po_no].apply(normalize_id)
    df_ap_invoice["clean_ap_invoice_no"] = df_ap_invoice[col_ap_invoice_no].apply(normalize_id)
    df_ap_invoice["clean_item_code"] = df_ap_invoice[col_ap_item_code].apply(normalize_id)

    # Filter base to rows that have GRPO Number
    df_base = df_ap_invoice[df_ap_invoice["clean_grpo_no"] != ""].copy()
    if df_base.empty:
        return {
            "rows": [],
            "kpis": kpis
        }

    # 2. Column lookups for GRPO Report
    grpo_dates = {}
    grpo_lines = {}
    if df_grpo is not None and not df_grpo.empty:
        col_grpo_no = find_col(df_grpo, ["GRPO No", "GRPO Number", "Goods Receipt No"]) or "GRPO No"
        col_grpo_item = find_col(df_grpo, ["Item Code", "Item No"]) or "Item Code"
        col_grpo_posting_date = find_col(df_grpo, ["Posting Date", "Document Date", "Date"]) or "Posting Date"
        col_grpo_qty = find_col(df_grpo, ["PO Qty", "PO Quantity", "Qty", "Quantity", "Received Qty"]) or "PO Qty"
        col_grpo_price = find_col(df_grpo, ["PO Price", "PO Rate", "Price", "Rate", "Received Price"]) or "PO Price"

        df_grpo = df_grpo.copy()
        df_grpo["clean_grpo_no"] = df_grpo[col_grpo_no].apply(normalize_id)
        df_grpo["clean_item_code"] = df_grpo[col_grpo_item].apply(normalize_id)

        # GRPO Dates mapping (take first posting date per GRPO No)
        grpo_dates = df_grpo.dropna(subset=["clean_grpo_no"]).drop_duplicates(subset=["clean_grpo_no"]).set_index("clean_grpo_no")[col_grpo_posting_date].to_dict()

        # GRPO Lines lookup
        for _, row in df_grpo.iterrows():
            k = (row["clean_grpo_no"], row["clean_item_code"])
            if k not in grpo_lines:
                grpo_lines[k] = {
                    "qty": parse_num(row.get(col_grpo_qty)),
                    "price": parse_num(row.get(col_grpo_price))
                }

    # 3. Column lookups for Purchase Order Report
    po_dates = {}
    po_lines = {}
    if df_po is not None and not df_po.empty:
        col_po_no = find_col(df_po, ["PO No", "PO Number", "Purchase Order No"]) or "PO No"
        col_po_item = find_col(df_po, ["Item Code", "Item No"]) or "Item Code"
        col_po_posting_date = find_col(df_po, ["Posting Date", "Document Date", "Date"]) or "Posting Date"
        col_po_vendor_code = find_col(df_po, ["Vendor Code", "BP Code"]) or "Vendor Code"
        col_po_vendor_name = find_col(df_po, ["Vendor Name", "BP Name"]) or "Vendor Name"
        col_po_currency = find_col(df_po, ["Document Currency", "BP Currency", "Currency"]) or "Document Currency"
        col_po_item_desc = find_col(df_po, ["Item Description", "Description"]) or "Item Description"
        col_po_item_group = find_col(df_po, ["Item Group", "Group"]) or "Item Group"
        col_po_qty = find_col(df_po, ["PO Qty", "PO Quantity", "Qty"]) or "PO Qty"
        col_po_price = find_col(df_po, ["PO Price", "PO Rate", "Price"]) or "PO Price"

        df_po = df_po.copy()
        df_po["clean_po_no"] = df_po[col_po_no].apply(normalize_id)
        df_po["clean_item_code"] = df_po[col_po_item].apply(normalize_id)

        # PO Dates mapping
        po_dates = df_po.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_po_posting_date].to_dict()

        # PO Lines lookup
        for _, row in df_po.iterrows():
            k = (row["clean_po_no"], row["clean_item_code"])
            if k not in po_lines:
                po_lines[k] = {
                    "vendor_code": str(row.get(col_po_vendor_code, "")).strip(),
                    "vendor_name": str(row.get(col_po_vendor_name, "")).strip(),
                    "currency": str(row.get(col_po_currency, "")).strip().upper(),
                    "item_desc": str(row.get(col_po_item_desc, "")).strip(),
                    "item_group": str(row.get(col_po_item_group, "")).strip(),
                    "qty": parse_num(row.get(col_po_qty)),
                    "price": parse_num(row.get(col_po_price))
                }

    # 4. Column lookups for Gate Entry Report
    gate_entry_dates = {}
    if df_gate_entry is not None and not df_gate_entry.empty:
        col_ge_po = find_col(df_gate_entry, ["Purchase Order Number", "Purchase Order No", "PO Number", "PO No"]) or "Purchase Order Number"
        col_ge_date = find_col(df_gate_entry, ["Gate Entry Date", "GE Date", "Date"]) or "Gate Entry Date"

        df_gate_entry = df_gate_entry.copy()
        df_gate_entry["clean_po_no"] = df_gate_entry[col_ge_po].apply(normalize_id)
        gate_entry_dates = df_gate_entry.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_ge_date].to_dict()

    # 5. Column lookups for AP Credit Note
    credit_notes = {}
    if df_credit_note is not None and not df_credit_note.empty:
        col_cn_ap_no = find_col(df_credit_note, ["AP Invoice Number", "AP Invoice No"]) or "AP Invoice Number"
        col_cn_no = find_col(df_credit_note, ["AP Credit Note No", "AP Credit Note Number", "Credit Note No"]) or "AP Credit Note No"

        df_credit_note = df_credit_note.copy()
        df_credit_note["clean_ap_invoice_no"] = df_credit_note[col_cn_ap_no].apply(normalize_id)
        credit_notes = df_credit_note.dropna(subset=["clean_ap_invoice_no"]).drop_duplicates(subset=["clean_ap_invoice_no"]).set_index("clean_ap_invoice_no")[col_cn_no].to_dict()

    # 6. Invoice Date mapping: from AP Invoice sheet from column posting date using PO Number (first date)
    ap_invoice_dates = df_ap_invoice.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")[col_ap_posting_date].to_dict()

    # Process base lines
    out_rows = []
    unique_po_set = set()
    unique_grn_set = set()
    unique_cn_set = set()
    unique_po_flagged_set = set()
    unique_grn_flagged_set = set()
    perfect_qty_sum = 0.0

    for _, row in df_base.iterrows():
        clean_po = row["clean_po_no"]
        clean_grpo = row["clean_grpo_no"]
        clean_item = row["clean_item_code"]
        clean_ap = row["clean_ap_invoice_no"]

        # PO & GRPO matches
        po_info = po_lines.get((clean_po, clean_item))
        grpo_info = grpo_lines.get((clean_grpo, clean_item))

        # Vendor and Country details (with fallback to AP Invoice report)
        vendor_code = po_info["vendor_code"] if po_info else str(row.get(col_ap_vendor_code, "")).strip()
        vendor_name = po_info["vendor_name"] if po_info else str(row.get(col_ap_vendor_name, "")).strip()
        currency = po_info["currency"] if po_info else str(row.get(col_ap_currency, "")).strip().upper()
        
        vendor_country = ""
        if currency:
            vendor_country = "India" if currency == "INR" else "USA"

        # Item info
        item_code = row[col_ap_item_code]
        item_desc = po_info["item_desc"] if po_info else str(row.get(col_ap_item_desc, ""))
        item_group = po_info["item_group"] if po_info else str(row.get(col_ap_item_group, ""))

        # Quantities
        po_qty = po_info["qty"] if po_info else 0.0
        grpo_qty = grpo_info["qty"] if grpo_info else 0.0
        inv_qty = parse_num(row.get(col_ap_qty))

        qty_po_gt_grpo = 1 if po_qty > grpo_qty else 0
        qty_grpo_gt_inv = 1 if grpo_qty > inv_qty else 0

        # Rates
        po_rate = po_info["price"] if po_info else 0.0
        grpo_rate = grpo_info["price"] if grpo_info else 0.0
        inv_rate = parse_num(row.get(col_ap_price))

        # Excess over 5% pricing discrepancy flag
        excess_over_5 = 0
        if grpo_rate > 0:
            if inv_rate > 1.05 * grpo_rate:
                excess_over_5 = 1
        elif inv_rate > 0:
            excess_over_5 = 1

        # Match Status
        # Check if PO qty, GRPO qty and Invoice qty are identical
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
            "grn_number": row[col_ap_grpo_no],
            "grpo_date": str(grpo_date_val) if not is_nan_or_none(grpo_date_val) else "",
            "po_number": row[col_ap_po_no],
            "po_date": str(po_date_val) if not is_nan_or_none(po_date_val) else "",
            "gate_entry_date": str(gate_entry_date_val) if not is_nan_or_none(gate_entry_date_val) else "",
            "invoice_date": str(invoice_date_val) if not is_nan_or_none(invoice_date_val) else "",
            "ap_invoice_number": row[col_ap_invoice_no],
            "ap_credit_note": credit_note_str,
            "vendor_code": vendor_code,
            "vendor_name": vendor_name,
            "vendor_country": vendor_country,
            "item_code": item_code,
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

    # Sort rows by grn_number and item_code for consistency
    out_rows.sort(key=lambda x: (str(x["grn_number"]), str(x["item_code"])))

    # Save calculated KPIs
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
