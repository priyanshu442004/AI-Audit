from __future__ import annotations
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

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

def parse_date(val, cache=None):
    if is_nan_or_none(val):
        return None
    val_str = str(val).strip()
    if val_str.lower() in ("nan", "none", "", "—"):
        return None
    
    if cache is not None and val_str in cache:
        return cache[val_str]
        
    for fmt in ('%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
        try:
            dt = datetime.strptime(val_str, fmt)
            if cache is not None:
                cache[val_str] = dt
            return dt
        except ValueError:
            continue
            
    try:
        dt = pd.to_datetime(val_str, errors='coerce')
        if pd.isna(dt):
            res = None
        else:
            res = dt.to_pydatetime()
        if cache is not None:
            cache[val_str] = res
        return res
    except:
        if cache is not None:
            cache[val_str] = None
        return None

def parse_numeric_val(val) -> float:
    if is_nan_or_none(val):
        return 0.0
    if val == "":
        return 0.0
    try:
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return float(val)
    except:
        return 0.0

def run_payment_aging_domestic(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Computes Payment Aging (Domestic) analysis.
    Filters out any vendor where Vendor Country is not "India" (derived from Document Currency == "INR").
    Reconciles with PO and BP Master reports.
    """
    df_gl = dfs.get("general_ledger")
    df_po = dfs.get("purchase_order")
    df_bp = dfs.get("vendor_master")

    # Local date cache to speed up row-by-row date parsing
    date_cache = {}

    # 1. Load BP Master for payment terms
    bp_terms = {}
    if df_bp is not None and not df_bp.empty:
        col_bp_code = None
        for alias in ["bp code", "bp_code", "card code", "cardcode"]:
            for col in df_bp.columns:
                if str(col).lower().strip() == alias:
                    col_bp_code = col
                    break
            if col_bp_code:
                break
        
        col_pt_code = None
        for alias in ["payment terms code", "payment terms", "terms"]:
            for col in df_bp.columns:
                if str(col).lower().strip() == alias:
                    col_pt_code = col
                    break
            if col_pt_code:
                break
                
        if col_bp_code and col_pt_code:
            # Optimize BP Master load
            cols_to_use = list(set([col_bp_code, col_pt_code]))
            bp_records = df_bp[cols_to_use].to_dict('records')
            for row in bp_records:
                code = normalize_id(row.get(col_bp_code))
                term = str(row.get(col_pt_code, '')).strip()
                if code:
                    bp_terms[code] = term

    # 2. Load PO Report for country and vendor group
    po_vendor_info = {}
    if df_po is not None and not df_po.empty:
        col_vendor_code = None
        for alias in ["vendor code", "vendor_code", "card code", "cardcode"]:
            for col in df_po.columns:
                if str(col).lower().strip() == alias:
                    col_vendor_code = col
                    break
            if col_vendor_code:
                break
        
        col_currency = None
        for alias in ["document currency", "currency", "doc currency", "po currency"]:
            for col in df_po.columns:
                if str(col).lower().strip() == alias:
                    col_currency = col
                    break
            if col_currency:
                break

        col_vendor_group = None
        for alias in ["vendor group", "vendor_group", "group name", "groupname"]:
            for col in df_po.columns:
                if str(col).lower().strip() == alias:
                    col_vendor_group = col
                    break
            if col_vendor_group:
                break

        if col_vendor_code:
            # Optimize PO Report load
            cols_to_use = list(set([c for c in [col_vendor_code, col_currency, col_vendor_group] if c]))
            po_records = df_po[cols_to_use].to_dict('records')
            for row in po_records:
                vcode = normalize_id(row.get(col_vendor_code))
                if not vcode:
                    continue
                
                curr = ""
                if col_currency:
                    curr = str(row.get(col_currency, '')).strip()
                
                vgroup = ""
                if col_vendor_group:
                    vgroup = str(row.get(col_vendor_group, '')).strip()
                
                country = "India" if curr.upper() in ("INR", "") else "USA"
                
                if vcode not in po_vendor_info:
                    po_vendor_info[vcode] = {'country': country, 'group': vgroup}

    # 3. Parse General Ledger
    out_rows = []
    if df_gl is not None and not df_gl.empty:
        current_vendor_code = None
        current_vendor_name = None
        
        gl_rows = df_gl.values.tolist()
        
        for row in gl_rows:
            if not row:
                continue
            
            val0 = row[0]
            col0_val = str(val0).strip() if not is_nan_or_none(val0) else ""
            if col0_val == 'Vendor':
                current_vendor_code = normalize_id(row[1]) if len(row) > 1 else None
                val9 = row[9] if len(row) > 9 else None
                current_vendor_name = str(val9).strip() if not is_nan_or_none(val9) else ""
                continue
            
            if not col0_val or col0_val.lower() in ("nan", "none"):
                continue
                
            if current_vendor_code is None:
                continue

            post_dt = parse_date(col0_val, date_cache)
            if post_dt is None:
                continue
                
            posting_date_str = col0_val
            
            val1 = row[1] if len(row) > 1 else None
            val2 = row[2] if len(row) > 2 else None
            val5 = row[5] if len(row) > 5 else None
            val11 = row[11] if len(row) > 11 else None
            val12 = row[12] if len(row) > 12 else None
            val13 = row[13] if len(row) > 13 else None
            
            due_date_str = str(val1).strip() if not is_nan_or_none(val1) else ""
            doc_date_str = str(val2).strip() if not is_nan_or_none(val2) else ""
            doc_no = str(val5).strip() if not is_nan_or_none(val5) else ""
            debit_str = str(val11).strip() if not is_nan_or_none(val11) else ""
            credit_str = str(val12).strip() if not is_nan_or_none(val12) else ""
            cum_bal_str = str(val13).strip() if not is_nan_or_none(val13) else ""
            
            if not doc_no:
                val6 = row[6] if len(row) > 6 else None
                doc_no = str(val6).strip() if not is_nan_or_none(val6) else "—"

            v_info = po_vendor_info.get(current_vendor_code, {})
            country = v_info.get('country', 'India')
            
            if country != 'India':
                continue
                
            vendor_group = v_info.get('group', 'Domestic vendor')
            if not vendor_group or vendor_group.lower() in ('nan', 'none', ''):
                vendor_group = 'Domestic vendor'
                
            vendor_address = current_vendor_name if current_vendor_name else "—"
            payment_terms = bp_terms.get(current_vendor_code, '—')
            
            term_type = "Advance"
            term_days = 0
            if payment_terms and payment_terms != '—':
                term_clean = str(payment_terms).strip()
                match = re.search(r'net[- ]?(\d+)', term_clean, re.IGNORECASE)
                if match:
                    term_type = "Credit(Net)"
                    term_days = int(match.group(1))
                elif "net" in term_clean.lower():
                    term_type = "Credit(Net)"
                    num_match = re.search(r'\d+', term_clean)
                    if num_match:
                        term_days = int(num_match.group(0))
            
            doc_dt = parse_date(doc_date_str, date_cache)
            if doc_dt is None:
                doc_dt = post_dt
                doc_date_str = posting_date_str
            
            due_date_calc = doc_dt + timedelta(days=term_days)
                
            debit_val = parse_numeric_val(debit_str)
            credit_val = parse_numeric_val(credit_str)
            payment_date = "—"
            pay_dt = None
            if debit_val > 0:
                payment_date = doc_date_str
                pay_dt = doc_dt
                
            days_late = 0
            if pay_dt and due_date_calc:
                diff = (pay_dt - due_date_calc).days
                days_late = max(0, diff)
                
            actual_paid = debit_val if debit_val > 0 else 0.0
            outstanding = parse_numeric_val(cum_bal_str)
            
            if abs(outstanding) <= 0.01:
                status = "Fully paid"
            elif actual_paid == 0:
                status = "Open"
            else:
                status = "Partially paid"
                
            if days_late <= 15:
                aging_cat = "Overdue 0-15"
            elif days_late <= 30:
                aging_cat = "Overdue 16-30"
            elif days_late <= 45:
                aging_cat = "Overdue 31-45"
            elif days_late <= 60:
                aging_cat = "Overdue 46-60"
            elif days_late <= 90:
                aging_cat = "Overdue 61-90"
            else:
                aging_cat = "Overdue >90"
                
            out_rows.append({
                "vendor_code": current_vendor_code if current_vendor_code else "—",
                "vendor_name": current_vendor_name if current_vendor_name else "—",
                "vendor_country": country,
                "vendor_group": vendor_group,
                "vendor_address": vendor_address,
                "payment_terms": payment_terms if payment_terms else "—",
                "payment_term_type": term_type,
                "term_days": term_days,
                "invoice_doc_number": doc_no,
                "document_date": doc_date_str if doc_date_str else "—",
                "posting_date": posting_date_str if posting_date_str else "—",
                "due_date_doc_term": due_date_calc.strftime("%d/%m/%y") if due_date_calc else "—",
                "payment_date": payment_date,
                "days_late": days_late,
                "actual_paid": actual_paid,
                "outstanding": outstanding,
                "status": status,
                "aging_category": aging_cat
            })

    out_rows.sort(key=lambda x: (x["vendor_code"], x["posting_date"]))

    return {
        "rows": out_rows,
        "kpis": {}
    }
