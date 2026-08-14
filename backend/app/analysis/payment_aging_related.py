from __future__ import annotations
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

RELATED_PARTIES_NORMALIZED = {
    "ROYALUXLIGHTINGPVTLTD",
    "IKIOSOLUTIONSPVTLTD",
    "ROYALUXLIGHTINGPRIVATELIMITEDUNIT2",
    "IKIOSOLUTIONSPRIVATELIMITEDUNIT2"
}

def is_related_party(name: str) -> bool:
    if not name:
        return False
    clean = re.sub(r'[^A-Z0-9]', '', name.upper())
    return clean in RELATED_PARTIES_NORMALIZED

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

def run_payment_aging_related(dfs: dict[str, pd.DataFrame]) -> dict:
    """
    Computes Payment Aging (Related Parties) analysis.
    Filters in only vendors matching the related parties list.
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
        gl_rows = df_gl.values.tolist()
        non_vendor_cats = {'Revenue', 'Asset', 'Equity', 'Expenditure', 'Liability', 'Customer'}
        
        # 1. Find max date in GL for reference
        col0_series = df_gl.iloc[:, 0].astype(str).str.strip()
        has_vendor_headers = (col0_series == 'Vendor').any()
        
        date_series = pd.to_datetime(col0_series, format='%d/%m/%y', errors='coerce')
        if date_series.dropna().empty:
            date_series = pd.to_datetime(col0_series, errors='coerce')
        valid_dates = date_series.dropna()
        reference_date = valid_dates.max().to_pydatetime() if not valid_dates.empty else datetime.today()
        
        # 2. Collect transactions grouped by vendor
        vendor_transactions = {}
        vendor_names = {}
        
        # Load BP names dictionary
        bp_names_dict = {}
        if df_bp is not None and not df_bp.empty:
            col_bp_c = None
            for alias in ["bp code", "bp_code", "card code", "cardcode"]:
                for col in df_bp.columns:
                    if str(col).lower().strip() == alias:
                        col_bp_c = col
                        break
                if col_bp_c: break
            col_bp_n = None
            for alias in ["bp name", "bp_name", "card name", "cardname"]:
                for col in df_bp.columns:
                    if str(col).lower().strip() == alias:
                        col_bp_n = col
                        break
                if col_bp_n: break
            if col_bp_c and col_bp_n:
                for _, bp_r in df_bp.iterrows():
                    c_code = normalize_id(bp_r.get(col_bp_c))
                    c_name = str(bp_r.get(col_bp_n, '')).strip()
                    if c_code: bp_names_dict[c_code] = c_name
        
        if has_vendor_headers:
            current_vendor_code = None
            current_vendor_name = None
            for row in gl_rows:
                if not row:
                    continue
                val0 = row[0]
                col0_val = str(val0).strip() if not is_nan_or_none(val0) else ""
                if col0_val == 'Vendor':
                    current_vendor_code = normalize_id(row[1]) if len(row) > 1 else None
                    val9 = row[9] if len(row) > 9 else None
                    current_vendor_name = str(val9).strip() if not is_nan_or_none(val9) else ""
                    if current_vendor_code:
                        vendor_names[current_vendor_code] = current_vendor_name
                    continue
                elif col0_val in non_vendor_cats:
                    current_vendor_code = None
                    current_vendor_name = None
                    continue
                    
                if current_vendor_code is None:
                    continue
                    
                post_dt = parse_date(col0_val, date_cache)
                if post_dt is None:
                    continue
                    
                if not is_related_party(current_vendor_name):
                    continue
                    
                if current_vendor_code not in vendor_transactions:
                    vendor_transactions[current_vendor_code] = []
                vendor_transactions[current_vendor_code].append(row)
        else:
            col_bp_idx = None
            for idx, col_name in enumerate(df_gl.columns):
                c_clean = str(col_name).lower().strip()
                if any(alias in c_clean for alias in ["g/l acct/bp code", "bp code", "card code", "cardcode", "vendor code"]):
                    col_bp_idx = idx
                    break
                    
            if col_bp_idx is not None:
                for row in gl_rows:
                    if not row or len(row) <= col_bp_idx:
                        continue
                    code_val = row[col_bp_idx]
                    if is_nan_or_none(code_val):
                        continue
                    c_str = normalize_id(code_val)
                    if not c_str:
                        continue
                        
                    v_name = bp_names_dict.get(c_str, "")
                    if not v_name and len(row) > 9 and not is_nan_or_none(row[9]) and str(row[9]).strip() not in ("nan", "None", ""):
                        v_name = str(row[9]).strip()

                    if not is_related_party(v_name):
                        continue
                        
                    if c_str.upper().startswith("V") or c_str in bp_names_dict or c_str in bp_terms:
                        val0 = row[0]
                        col0_val = str(val0).strip() if not is_nan_or_none(val0) else ""
                        post_dt = parse_date(col0_val, date_cache)
                        if post_dt is not None:
                            if c_str not in vendor_transactions:
                                vendor_transactions[c_str] = []
                                vendor_names[c_str] = v_name
                            vendor_transactions[c_str].append(row)
            
        # 3. Process each vendor's transactions using backward allocation
        for vcode, txs in vendor_transactions.items():
            if not txs:
                continue
            
            last_tx = txs[-1]
            final_bal = parse_numeric_val(last_tx[13])
            
            v_name = vendor_names.get(vcode, "—")
            v_info = po_vendor_info.get(vcode, {})
            country = v_info.get('country', 'India')
            vendor_group = v_info.get('group', 'Related vendor')
            if not vendor_group or vendor_group.lower() in ('nan', 'none', ''):
                vendor_group = 'Related vendor'
                
            vendor_address = v_name
            payment_terms = bp_terms.get(vcode, '—')
            
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
            
            # Find all credit/invoice transactions
            credits = []
            for idx, tx in enumerate(txs):
                credit = parse_numeric_val(tx[12])
                if credit > 0:
                    credits.append((idx, tx, credit))
            
            allocated_map = {}
            if final_bal < 0:
                liability = abs(final_bal)
                allocated = 0.0
                for idx, tx, credit in reversed(credits):
                    to_alloc = min(credit, liability - allocated)
                    allocated_map[idx] = to_alloc
                    allocated += to_alloc
                    if allocated >= liability:
                        break
                
                if allocated < liability:
                    remaining = liability - allocated
                    first_tx = txs[0]
                    date_str = str(first_tx[2]).strip() if not is_nan_or_none(first_tx[2]) else str(first_tx[0]).strip()
                    
                    due_date_calc = parse_date(date_str, date_cache)
                    days_late = 0
                    if due_date_calc and reference_date and reference_date > due_date_calc:
                        days_late = (reference_date - due_date_calc).days
                    
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
                        "vendor_code": vcode,
                        "vendor_name": v_name,
                        "vendor_country": country,
                        "vendor_group": vendor_group,
                        "vendor_address": vendor_address,
                        "payment_terms": payment_terms if payment_terms else "—",
                        "payment_term_type": term_type,
                        "term_days": term_days,
                        "invoice_doc_number": "Opening Balance",
                        "document_date": date_str,
                        "posting_date": date_str,
                        "due_date_doc_term": date_str,
                        "payment_date": "—",
                        "days_late": days_late,
                        "actual_paid": 0.0,
                        "outstanding": remaining,
                        "status": "Open",
                        "aging_category": aging_cat
                    })
            elif final_bal > 0:
                last_tx = txs[-1]
                date_str = str(last_tx[2]).strip() if not is_nan_or_none(last_tx[2]) else str(last_tx[0]).strip()
                out_rows.append({
                    "vendor_code": vcode,
                    "vendor_name": v_name,
                    "vendor_country": country,
                    "vendor_group": vendor_group,
                    "vendor_address": vendor_address,
                    "payment_terms": payment_terms if payment_terms else "—",
                    "payment_term_type": term_type,
                    "term_days": term_days,
                    "invoice_doc_number": "Advance",
                    "document_date": date_str,
                    "posting_date": date_str,
                    "due_date_doc_term": date_str,
                    "payment_date": "—",
                    "days_late": 0,
                    "actual_paid": 0.0,
                    "outstanding": final_bal,
                    "status": "Advance",
                    "aging_category": "Overdue 0-15"
                })
                
            for idx, tx, credit in credits:
                allocated = allocated_map.get(idx, 0.0)
                outstanding = allocated
                actual_paid = credit - outstanding
                
                # Payment date: search forward for first debit > 0
                payment_date_str = "—"
                pay_dt = None
                for f_tx in txs[idx+1:]:
                    f_debit = parse_numeric_val(f_tx[11])
                    if f_debit > 0:
                        payment_date_str = str(f_tx[2]).strip() if not is_nan_or_none(f_tx[2]) else str(f_tx[0]).strip()
                        pay_dt = parse_date(payment_date_str, date_cache)
                        break
                        
                status = "Fully paid" if outstanding <= 0.01 else ("Open" if actual_paid <= 0.01 else "Partially paid")
                
                doc_date_str = str(tx[2]).strip() if not is_nan_or_none(tx[2]) else str(tx[0]).strip()
                posting_date_str = str(tx[0]).strip() if not is_nan_or_none(tx[0]) else str(tx[2]).strip()
                
                doc_dt = parse_date(doc_date_str, date_cache)
                post_dt = parse_date(posting_date_str, date_cache)
                if doc_dt is None:
                    doc_dt = post_dt
                    
                due_date_calc = doc_dt + timedelta(days=term_days) if doc_dt else None
                
                # Compute days_late
                days_late = 0
                if status in ("Open", "Partially paid"):
                    if due_date_calc and reference_date and reference_date > due_date_calc:
                        days_late = (reference_date - due_date_calc).days
                elif status == "Fully paid":
                    if pay_dt and due_date_calc and pay_dt > due_date_calc:
                        days_late = (pay_dt - due_date_calc).days
                
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
                    "vendor_code": vcode,
                    "vendor_name": v_name,
                    "vendor_country": country,
                    "vendor_group": vendor_group,
                    "vendor_address": vendor_address,
                    "payment_terms": payment_terms if payment_terms else "—",
                    "payment_term_type": term_type,
                    "term_days": term_days,
                    "invoice_doc_number": str(tx[5]).strip() if not is_nan_or_none(tx[5]) else "—",
                    "document_date": doc_date_str,
                    "posting_date": posting_date_str,
                    "due_date_doc_term": due_date_calc.strftime("%d/%m/%y") if due_date_calc else "—",
                    "payment_date": payment_date_str,
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
