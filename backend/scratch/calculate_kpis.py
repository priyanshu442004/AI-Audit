import pickle
import os

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

for fname in ["aging_domestic.pkl", "aging_foreign.pkl", "aging_related.pkl", "aging_msme.pkl"]:
    path = os.path.join(cache_dir, fname)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        rows = data.get("rows", [])
        
        # Sort by vendor_code and posting_date as in JS or python (already sorted in python)
        # We take the last transaction for each vendor code
        vendor_balances = {}
        vendor_overdue = {}
        vendor_group = {}
        
        # Find max date
        dates = []
        for r in rows:
            date_str = r.get("posting_date") or r.get("document_date")
            # Simple parse
            if date_str and date_str != '—':
                import pandas as pd
                try:
                    dates.append(pd.to_datetime(date_str, format="%d/%m/%y"))
                except:
                    try:
                        dates.append(pd.to_datetime(date_str))
                    except:
                        pass
        
        max_date = max(dates) if dates else None
        
        for r in rows:
            vcode = r.get("vendor_code")
            if not vcode:
                continue
            bal = abs(float(r.get("outstanding") or 0.0))
            vendor_balances[vcode] = bal
            
            # check overdue
            status = r.get("status")
            if status in ('Open', 'Partially paid'):
                due_str = r.get("due_date_doc_term") or r.get("due_date")
                if due_str and due_str != '—' and max_date:
                    import pandas as pd
                    try:
                        due_dt = pd.to_datetime(due_str, format="%d/%m/%y")
                    except:
                        try:
                            due_dt = pd.to_datetime(due_str)
                        except:
                            due_dt = None
                    if due_dt and due_dt < max_date:
                        vendor_overdue[vcode] = True

        total_outstanding = sum(vendor_balances.values())
        overdue_amt = 0.0
        overdue_vendors_count = 0
        for vcode, bal in vendor_balances.items():
            if vendor_overdue.get(vcode):
                overdue_amt += bal
                overdue_vendors_count += 1
                
        print(f"{fname}:")
        print(f"  Total unique vendors: {len(vendor_balances)}")
        print(f"  Total Outstanding sum: {total_outstanding:.2f} (in Cr: {total_outstanding/1e7:.2f})")
        print(f"  Overdue sum: {overdue_amt:.2f} (in Cr: {overdue_amt/1e7:.2f})")
        print(f"  Overdue vendors count: {overdue_vendors_count}")
