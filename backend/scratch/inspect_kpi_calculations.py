import pickle
import pandas as pd
import os
from datetime import datetime

cache_dir = r"c:\Users\hp\Desktop\Audit\backend\.cache_dfs"

def parse_date(date_str):
    if not date_str or date_str == '—':
        return None
    s = str(date_str).strip()
    if not s or s.lower() in ('nan', 'none'):
        return None
    for fmt in ('%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(s).to_pydatetime()
    except:
        return None

# Load MSME
with open(os.path.join(cache_dir, "aging_msme.pkl"), "rb") as f:
    msme_data = pickle.load(f)
    
rows = msme_data["rows"]
print("Total MSME rows:", len(rows))

dates = [parse_date(r.get("posting_date") or r.get("document_date")) for r in rows]
dates = [d for d in dates if d is not None]
max_date = max(dates) if dates else datetime.now()
print("Max MSME Date:", max_date)

breaches = 0
for r in rows:
    doc_dt = parse_date(r.get("document_date") or r.get("posting_date"))
    if not doc_dt:
        continue
    
    is_paid = r.get("status") == "Fully paid" or (r.get("payment_date") and r.get("payment_date") != "—")
    if is_paid:
        pay_dt = parse_date(r.get("payment_date"))
        if pay_dt:
            diff = (pay_dt - doc_dt).days
            if diff > 45:
                breaches += 1
    else:
        diff = (max_date - doc_dt).days
        if diff > 45:
            breaches += 1

print("Calculated MSME breaches:", breaches)

# Load three_way_matching
with open(os.path.join(cache_dir, "three_way_matching.pkl"), "rb") as f:
    tw_data = pickle.load(f)

tw_rows = tw_data["rows"]
print("Total 3-way rows:", len(tw_rows))

qty_above_5 = 0
for r in tw_rows:
    po_qty = float(r.get("po_qty") or 0)
    grpo_qty = float(r.get("grpo_qty") or 0)
    if po_qty > 0:
        variance_pct = (abs(po_qty - grpo_qty) / po_qty) * 100
        if variance_pct > 5.0:
            qty_above_5 += 1

print("Calculated Quantity Deviations (>5% and po_qty > 0):", qty_above_5)

# What if po_qty is 0 but grpo_qty > 0?
qty_deviation_any = 0
for r in tw_rows:
    po_qty = float(r.get("po_qty") or 0)
    grpo_qty = float(r.get("grpo_qty") or 0)
    if po_qty > 0:
        variance_pct = (abs(po_qty - grpo_qty) / po_qty) * 100
        if variance_pct > 5.0:
            qty_deviation_any += 1
    elif grpo_qty > 0:
        qty_deviation_any += 1

print("Calculated Quantity Deviations (including po_qty == 0):", qty_deviation_any)

# Check price_variance_same savings using spread_gt_5
with open(os.path.join(cache_dir, "price_variance_same.pkl"), "rb") as f:
    pvs_data = pickle.load(f)

pvs_rows = pvs_data["rows"]
pvs_savings = 0
pvs_flagged_count = 0
for r in pvs_rows:
    if r.get("spread_gt_5") == 1:
        pvs_flagged_count += 1
        avg = float(r.get("avg_price") or 0)
        min_p = float(r.get("min_price") or 0)
        qty = float(r.get("ordered_qty") or 0)
        saving = (avg - min_p) * qty
        if saving > 0:
            pvs_savings += saving

print(f"Same-vendor price variance flagged count: {pvs_flagged_count}, savings: {pvs_savings}")

# Check price_variance_cross savings using higher_gt_5
with open(os.path.join(cache_dir, "price_variance_cross.pkl"), "rb") as f:
    pvc_data = pickle.load(f)

pvc_rows = pvc_data["rows"]
pvc_savings = 0
pvc_flagged_count = 0
for r in pvc_rows:
    if r.get("higher_gt_5") == 1:
        pvc_flagged_count += 1
        rate = float(r.get("rate_inr") or 0)
        min_p = float(r.get("item_min_rate") or 0)
        qty = float(r.get("ordered_qty") or 0)
        saving = (rate - min_p) * qty
        if saving > 0:
            pvc_savings += saving

print(f"Cross-vendor price variance flagged count: {pvc_flagged_count}, savings: {pvc_savings}")
