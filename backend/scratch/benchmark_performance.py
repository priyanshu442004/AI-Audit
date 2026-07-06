import os
import sys
import time
import httpx
import concurrent.futures
from dotenv import load_dotenv

# Ensure backend root is in import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

EXCEL_DIR = r"C:\Users\hp\Desktop\excel files"
FILE_MAPPING = {
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

def benchmark():
    client = httpx.Client(timeout=600.0)
    
    # 1. Clear Database
    print("Clearing database history...")
    import psycopg2
    from app.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE s3_uploaded_files RESTART IDENTITY;")
    conn.commit()
    cur.close()
    conn.close()
    
    # Invalidate cache directory to test first-run download/parse and then subsequent cached run
    import shutil
    from app.main import CACHE_DIR
    if os.path.exists(CACHE_DIR):
        print("Clearing local cache directory for clean benchmarking...")
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR, exist_ok=True)
    print("Database and local cache cleared.\n")
    
    # 2. Benchmark Upload
    print("Benchmark 1: Uploading 9 files in a single batch (with concurrent parsing + pickle caching + S3 transfer)...")
    files_payload = []
    
    for role, filename in FILE_MAPPING.items():
        filepath = os.path.join(EXCEL_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Error: {filepath} does not exist.")
            return
        
        # Read file bytes
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Use simpler (name, (filename, content)) tuple
        files_payload.append(('files', (filename, content)))
        
    data_payload = {'roles': list(FILE_MAPPING.keys())}
        
    start_time = time.time()
    try:
        response = client.post(
            f"{backend_url}/api/upload",
            files=files_payload,
            data=data_payload
        )
        upload_time = time.time() - start_time
        if response.status_code == 200:
            print(f"SUCCESS: Uploaded and cached 9 files in {upload_time:.2f} seconds.")
            upload_res = response.json()
            uploaded_files = upload_res.get("files", [])
        else:
            print(f"FAILED: Upload status code {response.status_code}, response: {response.text}")
            return
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED: Upload error: {e}")
        return
        
    # 3. Benchmark Ingestion / Pipeline Load
    print("\nBenchmark 2: Triggering analytical pipeline stream (should load instantly from local cache)...")
    start_time = time.time()
    try:
        # Trigger SSE stream
        with client.stream("GET", f"{backend_url}/api/analyze/combined") as r:
            for line in r.iter_lines():
                if line:
                    print(f"  Stream event: {line}")
        pipeline_time = time.time() - start_time
        print(f"SUCCESS: Pipeline completed in {pipeline_time:.2f} seconds.")
    except Exception as e:
        print(f"FAILED: Pipeline error: {e}")
        
    # 4. Benchmark Deletion
    print("\nBenchmark 3: Deleting uploaded files concurrently...")
    file_ids = [f["id"] for f in uploaded_files]
    print(f"Deleting file IDs: {file_ids}")
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(file_ids)) as executor:
        futures = []
        for fid in file_ids:
            futures.append(executor.submit(client.delete, f"{backend_url}/api/history/{fid}"))
        
        # Wait for all deletions to finish
        concurrent.futures.wait(futures)
            
    delete_time = time.time() - start_time
    print(f"SUCCESS: Deleted all {len(file_ids)} files concurrently in {delete_time:.2f} seconds.")

if __name__ == "__main__":
    benchmark()
