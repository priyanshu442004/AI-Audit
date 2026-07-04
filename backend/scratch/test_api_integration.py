import sys
import os
import httpx
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

def main():
    print("Testing backend API integration...")
    
    # Check if backend server is up
    url_health = f"{backend_url}/api/health"
    try:
        r = httpx.get(url_health)
        print(f"Health check status: {r.status_code}, response: {r.json()}")
    except Exception as e:
        print(f"ERROR: Backend server not running at {backend_url}: {e}")
        sys.exit(1)
        
    # Check uploaded files history
    url_history = f"{backend_url}/api/history"
    r = httpx.get(url_history)
    history = r.json()
    print(f"\nUpload history contains {len(history)} files.")
    
    # If history is empty, let's upload the files from C:\Users\hp\Desktop\excel files
    excel_dir = r"C:\Users\hp\Desktop\excel files"
    file_mapping = {
        'vendor_master': 'BP Master-ITL.csv',
        'purchase_order': 'Purchase Order Report-ITL.csv',
        'general_ledger': 'General Ledger ITL.csv',
    }
    
    active_roles = [f['role'] for f in history if not f.get('is_deleted', False)]
    needs_upload = False
    for role in file_mapping:
        if role not in active_roles:
            needs_upload = True
            break
            
    if needs_upload:
        print("\nUploading missing required files for analysis...")
        files_to_upload = []
        for role, filename in file_mapping.items():
            filepath = os.path.join(excel_dir, filename)
            if not os.path.exists(filepath):
                print(f"ERROR: Required file {filename} not found at {filepath}")
                sys.exit(1)
            files_to_upload.append(
                ("files", (filename, open(filepath, "rb"), "text/csv"))
            )
        
        # Call /api/upload
        r_upload = httpx.post(f"{backend_url}/api/upload", files=files_to_upload, data={"roles": list(file_mapping.keys())})
        if r_upload.status_code != 200:
            print(f"ERROR: File upload failed: {r_upload.status_code} - {r_upload.text}")
            sys.exit(1)
        print("Upload successful!")
        
    # Now query the new MSME Compliance analysis endpoint
    print("\nFetching payment aging (MSME Compliance) from /api/analysis/payment-aging-msme...")
    r_msme = httpx.get(f"{backend_url}/api/analysis/payment-aging-msme", timeout=60.0)
    
    if r_msme.status_code != 200:
        print(f"ERROR: API request failed with status {r_msme.status_code} - {r_msme.text}")
        sys.exit(1)
        
    result = r_msme.json()
    rows = result.get("rows", [])
    print(f"API returned {len(rows)} rows.")
    
    if len(rows) == 0:
        print("WARNING: API returned empty rows!")
        sys.exit(1)
        
    # Run assertions on the API output
    required_cols = [
        "vendor_code", "vendor_name", "vendor_country", "vendor_group", "vendor_address",
        "company_type", "payment_terms", "payment_term_type", "term_days", "invoice_doc_number",
        "document_date", "posting_date", "due_date_doc_term", "payment_date", "days_late",
        "actual_paid", "outstanding", "status", "aging_category"
    ]
    
    first_row = rows[0]
    missing = [c for c in required_cols if c not in first_row]
    assert not missing, f"Missing columns in API response row: {missing}"
    print("  [OK] All required columns are present in API response.")
    
    # Placement check
    keys = list(first_row.keys())
    assert keys.index("company_type") == keys.index("vendor_address") + 1, "company_type must follow vendor_address"
    print("  [OK] 'company_type' is placed correctly after 'vendor_address'.")
    
    unique_types = set()
    null_counts = {col: 0 for col in required_cols}
    for r in rows:
        unique_types.add(r["company_type"])
        for col in required_cols:
            val = r[col]
            if val is None or val == "" or (isinstance(val, float) and val != val):
                null_counts[col] += 1
                
    print(f"  [OK] Unique MSME company types in API response: {unique_types}")
    for ut in unique_types:
        assert ut.lower().strip() in ("micro", "small", "y"), f"Invalid company type: {ut}"
    print("  [OK] All rows are filtered to MSME vendors only.")
    
    print("\nNull counts in API response:")
    for col, count in null_counts.items():
        print(f"  - {col}: {count}")
        assert count == 0, f"Column '{col}' contains {count} empty/null values!"
    print("  [OK] No empty or null values found in any row.")
    
    print("\nAPI Integration Test Passed Successfully!")

if __name__ == "__main__":
    main()
