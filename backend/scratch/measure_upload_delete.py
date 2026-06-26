import os
import sys
import time
import httpx
import concurrent.futures

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

def run_test():
    client = httpx.Client(timeout=600.0)
    
    # 1. Clear database and cache
    import psycopg2
    from app.db import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE s3_uploaded_files RESTART IDENTITY;")
    conn.commit()
    cur.close()
    conn.close()
    
    import shutil
    from app.main import CACHE_DIR
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR, exist_ok=True)
        
    print("Database and cache cleared.")
    
    # 2. Upload Files
    files_payload = []
    for role, filename in FILE_MAPPING.items():
        filepath = os.path.join(EXCEL_DIR, filename)
        with open(filepath, 'rb') as f:
            content = f.read()
        files_payload.append(('files', (filename, content)))
        
    data_payload = {'roles': list(FILE_MAPPING.keys())}
    
    print("Uploading 9 files to `/api/upload`...")
    start_upload = time.time()
    try:
        response = client.post(
            "http://127.0.0.1:8000/api/upload",
            files=files_payload,
            data=data_payload
        )
        upload_time = time.time() - start_upload
        if response.status_code == 200:
            uploaded_files = response.json().get("files", [])
            print(f"UPLOAD SUCCESS: 9 files uploaded and cached in {upload_time:.3f} seconds.")
        else:
            print(f"UPLOAD FAILED: Status {response.status_code}, {response.text}")
            return
    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        return
        
    # 3. Delete Files
    file_ids = [f["id"] for f in uploaded_files]
    print(f"Deleting 9 files with IDs {file_ids} using DELETE `/api/history/{{id}}`...")
    start_delete = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(file_ids)) as executor:
        futures = [executor.submit(client.delete, f"http://127.0.0.1:8000/api/history/{fid}") for fid in file_ids]
        concurrent.futures.wait(futures)
        
    delete_time = time.time() - start_delete
    print(f"DELETE SUCCESS: 9 files deleted concurrently in {delete_time:.3f} seconds.")

if __name__ == "__main__":
    run_test()
