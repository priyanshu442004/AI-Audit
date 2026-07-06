import pandas as pd
import numpy as np
import os

folder = r"C:\Users\hp\Desktop\excel files"

# Load files
print("Loading files...")
df_ap_invoice = pd.read_csv(os.path.join(folder, "AP Invoice Report ITL.csv"))
df_grpo = pd.read_csv(os.path.join(folder, "GRPO Report ITL.csv"))
df_po = pd.read_csv(os.path.join(folder, "Purchase Order Report-ITL.csv"))
df_gate_entry = pd.read_csv(os.path.join(folder, "Gate Entry Report-ITL.csv"))
df_credit_note = pd.read_csv(os.path.join(folder, "AP Credit Note-ITL.csv"))

print(f"AP Invoice Report rows: {len(df_ap_invoice)}")
print(f"GRPO Report rows: {len(df_grpo)}")
print(f"Purchase Order Report rows: {len(df_po)}")
print(f"Gate Entry Report rows: {len(df_gate_entry)}")
print(f"AP Credit Note rows: {len(df_credit_note)}")

# Helper to clean and format strings to make joining robust
def clean_str_col(series):
    return series.astype(str).str.strip().str.replace(".0", "", regex=False).replace("nan", "")

# Apply basic string cleaning to join keys
df_ap_invoice["clean_grpo_no"] = clean_str_col(df_ap_invoice["GRPO Number"])
df_ap_invoice["clean_po_no"] = clean_str_col(df_ap_invoice["PO Number"])
df_ap_invoice["clean_ap_invoice_no"] = clean_str_col(df_ap_invoice["AP Invoice No"])
df_ap_invoice["clean_item_code"] = clean_str_col(df_ap_invoice["Item Code"])

df_grpo["clean_grpo_no"] = clean_str_col(df_grpo["GRPO No"])
df_grpo["clean_item_code"] = clean_str_col(df_grpo["Item Code"])

df_po["clean_po_no"] = clean_str_col(df_po["PO No"])
df_po["clean_item_code"] = clean_str_col(df_po["Item Code"])

df_gate_entry["clean_po_no"] = clean_str_col(df_gate_entry["Purchase Order Number"])

df_credit_note["clean_ap_invoice_no"] = clean_str_col(df_credit_note["AP Invoice Number"])
df_credit_note["clean_item_code"] = clean_str_col(df_credit_note["Item Code"])

# Prepare lookups or merged tables
# 1. GRPO Date from GRPO report page posting date using GRPO number
# Let's map clean_grpo_no -> Posting Date
# Since GRPO report might have multiple lines for same GRPO no, we can drop duplicates on clean_grpo_no to get a mapping.
grpo_dates = df_grpo.dropna(subset=["clean_grpo_no"]).drop_duplicates(subset=["clean_grpo_no"]).set_index("clean_grpo_no")["Posting Date"].to_dict()

# 2. Gate Entry Date from Gate Entry report using PO Number
# Only want 1 date if there are many? Let's get the first one for each PO.
gate_entry_dates = df_gate_entry.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")["Gate Entry Date"].to_dict()

# 3. Invoice Date from AP Invoice sheet from column posting date using PO Number, only want 1 date if there are many as others are same date
# Let's map clean_po_no -> Posting Date in AP Invoice Report
ap_invoice_dates = df_ap_invoice.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")["Posting Date"].to_dict()

# 4. AP Credit Note from AP Credit Note sheet from column AP Credit Note No using AP Invoice number
credit_notes = df_credit_note.dropna(subset=["clean_ap_invoice_no"]).drop_duplicates(subset=["clean_ap_invoice_no"]).set_index("clean_ap_invoice_no")["AP Credit Note No"].to_dict()

# Now construct the rows of the resultant table starting from df_ap_invoice (fetching all GRPO Numbers from AP Invoice Report)
# Wait, let's filter df_ap_invoice to only rows that have a GRPO number
df_base = df_ap_invoice[df_ap_invoice["clean_grpo_no"] != ""].copy()
print(f"Base rows with GRPO Number: {len(df_base)}")

# Let's join or lookup the remaining columns
# "GRPO Date"
df_base["GRPO Date"] = df_base["clean_grpo_no"].map(grpo_dates).fillna("")

# "PO Date"
# We need to lookup clean_po_no in Purchase Order Report to get Posting Date.
po_dates_dict = df_po.dropna(subset=["clean_po_no"]).drop_duplicates(subset=["clean_po_no"]).set_index("clean_po_no")["Posting Date"].to_dict()
df_base["PO Date"] = df_base["clean_po_no"].map(po_dates_dict).fillna("")

# "Gate Entry Date"
df_base["Gate Entry Date"] = df_base["clean_po_no"].map(gate_entry_dates).fillna("")

# "Invoice Date"
df_base["Invoice Date"] = df_base["clean_po_no"].map(ap_invoice_dates).fillna("")

# "AP Invoice Number"
df_base["AP Invoice Number"] = df_base["AP Invoice No"]

# "AP Credit Note"
df_base["AP Credit Note"] = df_base["clean_ap_invoice_no"].map(credit_notes).fillna("")

# For the columns below, we need details from Purchase Order Report matching (clean_po_no, clean_item_code)
# Let's build a lookup dictionary for PO lines: (clean_po_no, clean_item_code) -> PO row values
po_lines = {}
for idx, row in df_po.iterrows():
    k = (row["clean_po_no"], row["clean_item_code"])
    if k not in po_lines:
        po_lines[k] = row

# Similarly for GRPO lines: (clean_grpo_no, clean_item_code) -> GRPO row values
grpo_lines = {}
for idx, row in df_grpo.iterrows():
    k = (row["clean_grpo_no"], row["clean_item_code"])
    if k not in grpo_lines:
        grpo_lines[k] = row

# Populate columns:
# Vendo Code, Vendo Name, Vendor Country, Item code, Item description, Item group, PO qty, GRPO qty, Inv qty, Qty PO > GRPO, Qty GRPO > Inv, PO Rate (INR), GRPO Rate(INR), INV Rate(INR), Excess over 5%, Match Status

result_rows = []

def parse_num(v):
    if pd.isna(v):
        return 0.0
    s = str(v).replace(",", "").replace("₹", "").strip()
    try:
        return float(s)
    except:
        return 0.0

for idx, row in df_base.iterrows():
    clean_po = row["clean_po_no"]
    clean_grpo = row["clean_grpo_no"]
    clean_item = row["clean_item_code"]
    
    # lookup PO line
    po_row = po_lines.get((clean_po, clean_item))
    # lookup GRPO line
    grpo_row = grpo_lines.get((clean_grpo, clean_item))
    
    # Vendor Code and Name from PO report
    vendor_code = po_row["Vendor Code"] if po_row is not None else ""
    vendor_name = po_row["Vendor Name"] if po_row is not None else ""
    
    # Vendor Country: if currency is INR then India otherwise USA
    doc_currency = str(po_row["Document Currency"]).strip().upper() if po_row is not None else ""
    vendor_country = "India" if doc_currency == "INR" else ("USA" if doc_currency else "")
    
    # Item info
    item_code = po_row["Item Code"] if po_row is not None else row["Item Code"]
    item_desc = po_row["Item Description"] if po_row is not None else row["Item Description"]
    item_group = po_row["Item Group"] if po_row is not None else row["Item Group"]
    
    # Quantities
    po_qty = parse_num(po_row["PO Qty"]) if po_row is not None else 0.0
    grpo_qty = parse_num(grpo_row["PO Qty"]) if grpo_row is not None else 0.0
    inv_qty = parse_num(row["Invoice Qty"])
    
    # Flags
    qty_po_gt_grpo = 1 if po_qty > grpo_qty else 0
    qty_grpo_gt_inv = 1 if grpo_qty > inv_qty else 0
    
    # Rates
    po_rate = parse_num(po_row["PO Price"]) if po_row is not None else 0.0
    grpo_rate = parse_num(grpo_row["PO Price"]) if grpo_row is not None else 0.0
    inv_rate = parse_num(row["Invoice Price"])
    
    # Excess over 5%: if invoice rate is upto 5% greater than GRPO rate then 0, if more than 5% then 1
    # Let's be careful about grpo_rate == 0
    excess_over_5 = 0
    if grpo_rate > 0:
        # Check if invoice rate is more than 5% greater than GRPO rate
        if inv_rate > 1.05 * grpo_rate:
            excess_over_5 = 1
    elif inv_rate > 0:
        excess_over_5 = 1
        
    # Match Status: if PO rate, GRPO rate, and inv rate all are same then "Perfect match" otherwise "Variance"
    # Wait, let's use exact match or with small float tolerance? Since they are floats, let's compare with small delta
    if abs(po_rate - grpo_rate) < 1e-4 and abs(grpo_rate - inv_rate) < 1e-4:
        match_status = "Perfect match"
    else:
        match_status = "Variance"
        
    res_row = {
        "GRN Number": row["GRPO Number"],
        "GRPO Date": row["GRPO Date"],
        "PO Number": row["PO Number"],
        "PO Date": row["PO Date"],
        "Gate Entry Date": row["Gate Entry Date"],
        "Invoice Date": row["Invoice Date"],
        "AP Invoice Number": row["AP Invoice Number"],
        "AP Credit Note": row["AP Credit Note"],
        "Vendo Code": vendor_code,
        "Vendo Name": vendor_name,
        "Vendor Country": vendor_country,
        "Item code": item_code,
        "Item description": item_desc,
        "Item group": item_group,
        "PO qty": po_qty,
        "GRPO qty": grpo_qty,
        "Inv qty": inv_qty,
        "Qty PO > GRPO": qty_po_gt_grpo,
        "Qty GRPO > Inv": qty_grpo_gt_inv,
        "PO Rate (INR)": po_rate,
        "GRPO Rate(INR)": grpo_rate,
        "INV Rate(INR)": inv_rate,
        "Excess over 5%": excess_over_5,
        "Match Status": match_status
    }
    result_rows.append(res_row)

df_result = pd.DataFrame(result_rows)
print(f"Resulting table rows: {len(df_result)}")

# Top page items calculations:
# "Total GRPO Lines"-> which is count of total GRPO lines here (wait, total rows in resultant table?)
total_grpo_lines = len(df_result)
# "Perfect Match(QTY)"-> total quantity from Inv Qty where match status is perfect match
# Note: since the column name in result is "Match Status", let's sum "Inv qty"
perfect_match_qty = df_result[df_result["Match Status"] == "Perfect match"]["Inv qty"].sum()
# "unique PO Numbers"-> count of unique PO numbers in resultant table
unique_po_count = df_result["PO Number"].dropna().nunique()
# "Unique GRPO Numbers"-> count of unique GRPO numbers in resultant table
unique_grpo_count = df_result["GRN Number"].dropna().nunique()
# "Unique AP Credit Notes"-> count of unique AP Credit notes in resultant table
unique_credit_notes_count = df_result["AP Credit Note"].replace("", np.nan).dropna().nunique()
# "Unique PO Flagged"-> count of unique PO numbers where excess over 5% column is 1
unique_po_flagged = df_result[df_result["Excess over 5%"] == 1]["PO Number"].dropna().nunique()
# "Unique GRN flagged"-> count of unique GRPO numbers where excess over 5% column is 1
unique_grn_flagged = df_result[df_result["Excess over 5%"] == 1]["GRN Number"].dropna().nunique()

print(f"Total GRPO Lines: {total_grpo_lines}")
print(f"Perfect Match (QTY): {perfect_match_qty}")
print(f"Unique PO Numbers: {unique_po_count}")
print(f"Unique GRPO Numbers: {unique_grpo_count}")
print(f"Unique AP Credit Notes: {unique_credit_notes_count}")
print(f"Unique PO Flagged: {unique_po_flagged}")
print(f"Unique GRN flagged: {unique_grn_flagged}")

print("Done testing!")
