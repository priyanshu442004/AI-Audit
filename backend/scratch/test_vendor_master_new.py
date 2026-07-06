import os
import sys
import httpx
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

def main():
    print(f"Testing Vendor Master New API endpoint at {backend_url}...")
    
    # Check health first
    try:
        r_health = httpx.get(f"{backend_url}/api/health")
        print(f"Health check status: {r_health.status_code}, response: {r_health.json()}")
    except Exception as e:
        print(f"ERROR: Backend server not running at {backend_url}: {e}")
        sys.exit(1)

    print("\nFetching data from /api/analysis/vendor-master-new...")
    try:
        r = httpx.get(f"{backend_url}/api/analysis/vendor-master-new", timeout=60.0)
    except Exception as e:
        print(f"ERROR: API request failed: {e}")
        sys.exit(1)

    if r.status_code != 200:
        print(f"ERROR: API returned status {r.status_code} - {r.text}")
        sys.exit(1)

    data = r.json()
    rows = data.get("rows", [])
    kpis = data.get("kpis", {})

    print(f"\nAPI returned {len(rows)} rows.")
    print("KPIs:")
    for k, v in kpis.items():
        print(f"  - {k}: {v}")

    # Assertions
    assert len(rows) > 0, "No rows returned by API!"
    
    required_cols = [
        "vendor_code", "vendor_name", "vendor_country", "vendor_group", "region",
        "currency", "gstin", "msme_registration", "payment_terms", "active",
        "same_gst_multi_code", "missing_gstin", "foreign_w_gstin", "related_party"
    ]
    
    first_row = rows[0]
    print(f"\nFirst row keys: {list(first_row.keys())}")
    print(f"First row sample: {first_row}")

    missing_cols = [c for c in required_cols if c not in first_row]
    assert not missing_cols, f"Missing columns in API response rows: {missing_cols}"
    print("\n[OK] All required columns are present in the row schema.")

    # Check vendor codes start with V
    invalid_codes = [r["vendor_code"] for r in rows if not str(r["vendor_code"]).upper().startswith("V")]
    assert not invalid_codes, f"Found vendor codes not starting with 'V': {invalid_codes[:10]}"
    print("[OK] All vendor codes start with the letter 'V'.")

    # Check values for no empty/nulls (excluding columns that can naturally be empty in raw data but should have placeholders like '—')
    null_counts = {col: 0 for col in required_cols}
    for r in rows:
        for col in required_cols:
            val = r[col]
            if val is None or val == "" or (isinstance(val, float) and val != val):
                null_counts[col] += 1
                
    print("\nNull/Empty counts in response:")
    for col, count in null_counts.items():
        print(f"  - {col}: {count}")
        assert count == 0, f"Column '{col}' contains {count} empty/null values!"
    print("[OK] No empty or null values found in any row.")

    # Validation check for KPIs
    total_suppliers = kpis.get("total_suppliers")
    assert total_suppliers == len(rows), f"total_suppliers KPI {total_suppliers} does not match row count {len(rows)}!"
    print("[OK] total_suppliers KPI matches row count.")

    print("\nEnd-to-end API test for Vendor Master New passed successfully!")

if __name__ == "__main__":
    main()
