import os
import sys
import pandas as pd

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.payment_aging_msme import run_payment_aging_msme

def main():
    excel_dir = r"C:\Users\hp\Desktop\excel files"
    
    file_mapping = {
        'vendor_master': 'BP Master-ITL.csv',
        'purchase_order': 'Purchase Order Report-ITL.csv',
        'general_ledger': 'General Ledger ITL.csv',
    }
    
    print("Loading raw CSV files directly...")
    dfs = {}
    for role, filename in file_mapping.items():
        filepath = os.path.join(excel_dir, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: File {filename} not found at {filepath}!")
            sys.exit(1)
        dfs[role] = pd.read_csv(filepath, dtype=str)
        print(f"  Loaded {role}: {dfs[role].shape[0]} rows, {dfs[role].shape[1]} columns")

    print("\nRunning run_payment_aging_msme on loaded DataFrames...")
    result = run_payment_aging_msme(dfs)
    
    rows = result.get("rows", [])
    print(f"Generated {len(rows)} result rows.")
    
    if len(rows) == 0:
        print("WARNING: No rows generated in MSME Compliance!")
        return

    # Basic validations
    print("\nValidating results...")
    
    # 1. Check columns
    required_cols = [
        "vendor_code", "vendor_name", "vendor_country", "vendor_group", "vendor_address",
        "company_type", "payment_terms", "payment_term_type", "term_days", "invoice_doc_number",
        "document_date", "posting_date", "due_date_doc_term", "payment_date", "days_late",
        "actual_paid", "outstanding", "status", "aging_category"
    ]
    
    sample_row = rows[0]
    missing_cols = [col for col in required_cols if col not in sample_row]
    assert not missing_cols, f"Missing columns in output row: {missing_cols}"
    print("  [OK] All required columns are present in the output.")
    
    # 2. Check "Company Type" column placement
    keys = list(sample_row.keys())
    vendor_address_idx = keys.index("vendor_address")
    company_type_idx = keys.index("company_type")
    assert company_type_idx == vendor_address_idx + 1, "company_type must be placed immediately after vendor_address!"
    print("  [OK] 'company_type' is correctly located immediately after 'vendor_address'.")

    # 3. Check MSME Registration filter ("micro", "small", "y" only)
    unique_types = set()
    empty_company_types = 0
    empty_any_val = 0
    empty_cols = {col: 0 for col in required_cols}
    
    for idx, r in enumerate(rows):
        ctype = r["company_type"]
        unique_types.add(ctype)
        if not ctype or ctype == "-":
            empty_company_types += 1
        
        # Check all columns for empty/None/NaN values
        for col in required_cols:
            val = r[col]
            if val is None or val == "" or (isinstance(val, float) and val != val):
                empty_cols[col] += 1
                empty_any_val += 1
                
    print(f"  [OK] Unique MSME Company Types found: {unique_types}")
    for ut in unique_types:
        assert ut.lower().strip() in ("micro", "small", "y"), f"Invalid company type value found: {ut}"
    print("  [OK] All output rows belong to MSME vendors ('micro', 'small', or 'y').")
    
    # Ensure there are no empty company types
    assert empty_company_types == 0, f"Found {empty_company_types} rows with empty company type!"
    print("  [OK] No rows have empty company types.")
    
    # Check for empty columns
    print("\nEmpty/Null values count per column:")
    for col, count in empty_cols.items():
        print(f"  - {col}: {count}")
        # Note: payment_date and days_late can be 0 or '-' naturally. But let's assert no actual Python None/NaN.
        assert count == 0, f"Column '{col}' has {count} empty/null values!"
    print("  [OK] All column cells are correctly populated with non-null/non-empty values.")
    
    # Let's print a few sample rows to inspect
    print("\nSample MSME compliance rows:")
    for i in range(min(5, len(rows))):
        r = rows[i]
        print(f"\nRow {i+1}:")
        for col in required_cols:
            print(f"  {col}: {r[col]}")

if __name__ == "__main__":
    main()
