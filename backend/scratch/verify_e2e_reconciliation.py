import os
import io
import sys
import pandas as pd
from dotenv import load_dotenv

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environmental variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

from app.db import init_db, add_uploaded_file, get_active_files, delete_file, replace_file
from app.s3 import upload_file_to_s3, download_file_from_s3
from app.main import load_combined_dfs
from app.analysis.po_status import run as run_po_status
from app.analysis.gate_entry import run as run_gate_entry

def clean_database():
    print("Connecting to RDS and clearing uploaded files database history...")
    import psycopg2
    from app.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE s3_uploaded_files RESTART IDENTITY;")
    conn.commit()
    cur.close()
    conn.close()
    print("Database cleared successfully.")

def upload_test_files():
    excel_dir = r"C:\Users\hp\Desktop\excel files"
    file_mapping = {
        'ap_credit_note': 'AP Credit Note-ITL.csv',
        'ap_invoice_report': 'AP Invoice Report ITL.csv',
        'vendor_master': 'BP Master-ITL.csv',
        'gate_entry': 'Gate Entry Report-ITL.csv',
        'general_ledger': 'General Ledger ITL.csv',
        'grpo': 'GRPO Report ITL.csv',
        'item_master': 'Item Master-ITL.csv',
        'purchase_order': 'Purchase Order Report-ITL.csv',
        'purchase_register': 'Purchase Register -ITL.csv'
    }
    
    print(f"\nScanning test files in: {excel_dir}...")
    for role, filename in file_mapping.items():
        filepath = os.path.join(excel_dir, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: Missing file {filename} for role {role}")
            sys.exit(1)
            
        print(f"Reading and uploading {filename} ({role})...")
        with open(filepath, 'rb') as f:
            data = f.read()
            
        # Upload to S3
        s3_res = upload_file_to_s3(data, filename, role)
        
        # Record in RDS
        db_res = add_uploaded_file(role, filename, s3_res["s3_key"], s3_res["s3_url"], s3_res["row_count"])
        print(f"Successfully uploaded and registered: ID={db_res['id']}, Rows={db_res['row_count']}")

def run_e2e_reconciliation():
    print("\n-------------------------------------------------------------")
    print("Running Consolidated Analytical Pipeline on S3 Data...")
    print("-------------------------------------------------------------")
    
    # 1. Fetch from S3 & PostgreSQL
    dfs = load_combined_dfs()
    print(f"Loaded roles: {list(dfs.keys())}")
    for role, df in dfs.items():
        print(f"  - {role}: {df.shape[0]} rows, {df.shape[1]} columns")
        
    # 2. Run PO Status Analysis
    print("\nExecuting PO Status analysis...")
    po_res = run_po_status(dfs)
    po_kpis = po_res["kpis"]
    po_tables = po_res["tables"]
    
    print("\n=== PO Status KPIs ===")
    for k, v in po_kpis.items():
        print(f"  {k}: {v}")
        
    po_anal_table = None
    for t in po_tables:
        if t["title"] == "Purchase Order Line Status Analysis":
            po_anal_table = t
            break
            
    if po_anal_table:
        po_rows = po_anal_table["rows"]
        print(f"\nPO Line Analysis Table has {len(po_rows)} rows.")
        if len(po_rows) > 0:
            print("\nSample Row PO Line Analysis:")
            sample = po_rows[0]
            for col in ["PO Number", "Posting Date", "Gate Entry Date", "Doc Status", "GRN No.", "AP Invoice No.", "Line Value(INR)", "Holiday flag"]:
                print(f"  {col}: {sample.get(col)}")
                
            # Verify if Gate Entry Dates are populated for matched POs
            matched_ge = [r for r in po_rows if r.get("Gate Entry Date")]
            print(f"\nLines with Gate Entry Date populated: {len(matched_ge)} / {len(po_rows)}")
            if matched_ge:
                print("Sample Matched Gate Entry Row:")
                for col in ["PO Number", "Posting Date", "Gate Entry Date", "GRN No."]:
                    print(f"    {col}: {matched_ge[0].get(col)}")
    else:
        print("ERROR: PO Status Analysis table not found!")

    # 3. Run Gate Entry Analysis
    print("\nExecuting Gate Entry analysis...")
    ge_res = run_gate_entry(dfs)
    ge_kpis = ge_res["kpis"]
    ge_tables = ge_res["tables"]
    
    print("\n=== Gate Entry KPIs ===")
    for k, v in ge_kpis.items():
        print(f"  {k}: {v}")
        
    ge_anal_table = None
    for t in ge_tables:
        if t["title"] == "Gate Entry Full Transaction List":
            ge_anal_table = t
            break
            
    if ge_anal_table:
        ge_rows = ge_anal_table["rows"]
        print(f"\nGate Entry Matching Table has {len(ge_rows)} rows.")
        if len(ge_rows) > 0:
            print("\nSample Row Gate Entry:")
            sample = ge_rows[0]
            for col in ["Gate Entry number", "Gate Entry Date", "GRPO Date", "Days(GRPO-GE)", "Seq Exception(GE>GRPO)", "Value(INR)"]:
                print(f"  {col}: {sample.get(col)}")
    else:
        print("ERROR: Gate Entry Matching table not found!")

if __name__ == "__main__":
    init_db()
    clean_database()
    upload_test_files()
    run_e2e_reconciliation()
