"""FastAPI application — IKIO P2P Audit Dashboard API."""

from __future__ import annotations

import asyncio
import io
import json
import math
import os
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import pandas as pd
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

import app.session as session_store
from app.loaders import load_file
from app.pipeline import run_pipeline
from app.insights import generate_section_insight, generate_executive_summary
from app.config import FILE_ROLES
from app.db import init_db, add_uploaded_file, get_active_files, delete_file, delete_all_files, replace_file, get_file_by_id, add_audit_log, get_audit_logs
from app.s3 import upload_file_to_s3, download_file_from_s3

# Initialize the database on startup
init_db()

cached_dfs: dict[str, pd.DataFrame] | None = None
cached_aging_domestic: dict | None = None
cached_aging_foreign: dict | None = None
cached_aging_related: dict | None = None
cached_aging_msme: dict | None = None
cached_vendor_master_new: dict | None = None
cached_three_way_matching: dict | None = None
cached_price_variance_same: dict | None = None
cached_price_variance_cross: dict | None = None

def clear_calculation_caches():
    global cached_dfs, cached_aging_domestic, cached_aging_foreign, cached_aging_related, cached_aging_msme, cached_vendor_master_new, cached_three_way_matching, cached_price_variance_same, cached_price_variance_cross
    cached_dfs = None
    cached_aging_domestic = None
    cached_aging_foreign = None
    cached_aging_related = None
    cached_aging_msme = None
    cached_vendor_master_new = None
    cached_three_way_matching = None
    cached_price_variance_same = None
    cached_price_variance_cross = None
    
    # Invalidate session result
    combined_sess = session_store.get_session("combined")
    if combined_sess:
        combined_sess.result = None
        
    # Delete calculated cache files on disk
    calc_files = [
        "pipeline_result.pkl",
        "aging_domestic.pkl",
        "aging_foreign.pkl",
        "aging_related.pkl",
        "aging_msme.pkl",
        "vendor_master_new.pkl",
        "three_way_matching.pkl",
        "price_variance_same.pkl",
        "price_variance_cross.pkl"
    ]
    for fn in calc_files:
        p = os.path.join(CACHE_DIR, fn)
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                print(f"Failed to remove cache file {fn}: {e}")

def get_cached_dfs_or_load() -> dict[str, pd.DataFrame]:
    global cached_dfs
    if cached_dfs is None:
        cached_dfs = load_combined_dfs()
    return cached_dfs



class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that safely handles NaN, infinity, and other special values."""
    def encode(self, o):
        if isinstance(o, float):
            if math.isnan(o) or math.isinf(o):
                return 'null'
        return super().encode(o)
    
    def iterencode(self, o, _one_shot=False):
        """Override iterencode to handle NaN and infinity in nested structures."""
        for chunk in super().iterencode(o, _one_shot):
            yield chunk


def sanitize_for_json(obj):
    """
    Recursively sanitize objects to remove NaN and infinity values.
    Converts them to None (null in JSON).
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    else:
        return obj


import hashlib
import pickle

CACHE_DIR = os.path.join(os.path.dirname(__file__), "../.cache_dfs")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(s3_key: str) -> str:
    key_hash = hashlib.md5(s3_key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{key_hash}.pkl")

def load_combined_dfs(on_progress=None) -> dict[str, pd.DataFrame]:
    """
    Load all active S3 files concurrently, group them by role,
    and concatenate them into a combined dictionary of DataFrames.
    Uses a local pickle cache to speed up loads.
    """
    active_files = get_active_files()
    
    files_by_role = {}
    for f in active_files:
        role = f['role']
        if role not in files_by_role:
            files_by_role[role] = []
        files_by_role[role].append(f)
        
    flat_files = []
    for role, file_infos in files_by_role.items():
        # Sort by ID so older uploads are concatenated first
        for fi in sorted(file_infos, key=lambda x: x['id']):
            flat_files.append((role, fi))
            
    total_files = len(flat_files)
    dfs_lists = {}
    
    if total_files == 0:
        return {}

    import concurrent.futures

    def load_single_file(task_idx, role, fi):
        s3_key = fi['s3_key']
        cache_path = get_cache_path(s3_key)
        
        # 1. Try to load from cache
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    df = pickle.load(f)
                return role, df, fi['filename'], None
            except Exception as e:
                print(f"Failed to read cache for {fi['filename']}: {e}")
                
        # 2. Download from S3 and parse
        try:
            data = download_file_from_s3(s3_key)
            df = load_file(io.BytesIO(data), fi['filename'])
            
            # Save to cache for next time
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(df, f)
            except Exception as ce:
                print(f"Failed to write cache for {fi['filename']}: {ce}")
                
            return role, df, fi['filename'], None
        except Exception as e:
            return role, None, fi['filename'], e

    results_by_idx = [None] * total_files

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, total_files)) as executor:
        future_to_info = {}
        for idx, (role, fi) in enumerate(flat_files):
            fut = executor.submit(load_single_file, idx, role, fi)
            future_to_info[fut] = (idx, role, fi)
            
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_info):
            idx, role, fi = future_to_info[future]
            completed_count += 1
            if on_progress:
                try:
                    on_progress(fi['filename'], role, completed_count, total_files)
                except Exception:
                    pass
            try:
                role, df, filename, err = future.result()
                if err:
                    print(f"Error loading file {filename} for role {role}: {err}")
                else:
                    results_by_idx[idx] = df
            except Exception as e:
                print(f"Unexpected error in thread for {fi['filename']}: {e}")

    # Reassemble in the exact original order
    for idx, (role, fi) in enumerate(flat_files):
        df = results_by_idx[idx]
        if df is not None:
            if role not in dfs_lists:
                dfs_lists[role] = []
            dfs_lists[role].append(df)
            
    dfs = {}
    for role, role_dfs in dfs_lists.items():
        if role_dfs:
            if len(role_dfs) == 1:
                dfs[role] = role_dfs[0]
            else:
                dfs[role] = pd.concat(role_dfs, ignore_index=True)
                
    return dfs


app = FastAPI(title="IKIO P2P Audit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Upload ────────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    roles: list[str] = Form(...),
):
    """
    Upload files concurrently, save to S3, record in database,
    and invalidate the combined analysis cache.
    """
    if len(files) != len(roles):
        raise HTTPException(400, "files and roles must have equal length.")

    valid_roles = set(FILE_ROLES.keys())
    for r in roles:
        if r not in valid_roles:
            raise HTTPException(400, f"Unknown role '{r}'. Valid: {list(valid_roles)}")

    # Invalidate combined result cache
    clear_calculation_caches()

    loop = asyncio.get_running_loop()

    async def process_single(uf: UploadFile, r: str):
        data = await uf.read()
        try:
            # 1. Upload to S3 (blocking, run in thread pool)
            s3_res = await loop.run_in_executor(None, lambda: upload_file_to_s3(data, uf.filename, r))
            # 2. Add to Database (blocking, run in thread pool)
            db_res = await loop.run_in_executor(
                None, 
                lambda: add_uploaded_file(r, uf.filename, s3_res["s3_key"], s3_res["s3_url"], s3_res["row_count"])
            )
            # Log the upload
            await loop.run_in_executor(None, lambda: add_audit_log("File Uploaded", uf.filename, f"Uploaded under role {r}"))
            return {
                "id": db_res["id"],
                "role": db_res["role"],
                "filename": db_res["filename"],
                "s3Key": db_res["s3_key"],
                "s3Url": db_res["s3_url"],
                "rowCount": db_res["row_count"],
                "uploadedAt": str(db_res["uploaded_at"]),
            }
        except Exception as exc:
            raise HTTPException(422, f"Cannot process/upload '{uf.filename}': {exc}")

    tasks = [process_single(uf, r) for uf, r in zip(files, roles)]
    file_info = await asyncio.gather(*tasks)

    return {"session_id": "combined", "files": file_info}


# ── Upload Holidays ───────────────────────────────────────────────────────────
@app.post("/api/upload-holidays")
async def upload_holidays(file: UploadFile = File(...)):
    """
    Upload a holidays Excel/CSV file, clear existing files in backend/holidays/,
    and save the new file.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        raise HTTPException(400, "Unsupported file format. Please upload .xlsx, .xls, or .csv.")

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        holidays_dir = os.path.abspath(os.path.join(current_dir, "..", "holidays"))
        os.makedirs(holidays_dir, exist_ok=True)

        # Remove all existing files in the directory
        for old_file in os.listdir(holidays_dir):
            old_file_path = os.path.join(holidays_dir, old_file)
            if os.path.isfile(old_file_path):
                os.remove(old_file_path)

        new_file_path = os.path.join(holidays_dir, file.filename)
        data = await file.read()
        with open(new_file_path, "wb") as f:
            f.write(data)

        # Invalidate cache
        clear_calculation_caches()
        
        # Log the holiday file upload
        add_audit_log("Holidays Uploaded", file.filename, "Uploaded custom holidays list")

        return {"status": "success", "filename": file.filename, "message": "Holidays file uploaded and replaced successfully."}

    except Exception as e:
        raise HTTPException(500, f"Error uploading holidays file: {str(e)}")


@app.get("/api/holidays-info")
def get_holidays_info():
    """
    Get the name of the currently uploaded holidays file.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        holidays_dir = os.path.abspath(os.path.join(current_dir, "..", "holidays"))
        if os.path.exists(holidays_dir):
            files = os.listdir(holidays_dir)
            valid_files = [f for f in files if os.path.isfile(os.path.join(holidays_dir, f)) and f.lower().endswith(('.xlsx', '.xls', '.csv'))]
            if valid_files:
                return {"has_file": True, "filename": valid_files[0]}
        return {"has_file": False, "filename": None}
    except Exception as e:
        raise HTTPException(500, f"Error getting holidays info: {str(e)}")


# ── Audit History Management ──────────────────────────────────────────────────
@app.get("/api/history")
def list_history():
    """List all active uploaded files. Runs in standard threadpool."""
    try:
        files = get_active_files()
        return [
            {
                "id": f["id"],
                "role": f["role"],
                "filename": f["filename"],
                "s3Key": f["s3_key"],
                "s3Url": f["s3_url"],
                "rowCount": f["row_count"],
                "uploadedAt": str(f["uploaded_at"]),
            }
            for f in files
        ]
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.delete("/api/history/delete-all")
def delete_all_history_files():
    """Soft delete all active files from database and invalidate cached analysis."""
    try:
        deleted_count = delete_all_files()
        
        # Invalidate combined session cache
        clear_calculation_caches()
        
        # Log deletion
        add_audit_log("File Deleted", "All Active Files", f"Soft deleted all {deleted_count} active files")
            
        return {"status": "success", "message": f"Successfully deleted {deleted_count} files."}
    except Exception as e:
        raise HTTPException(500, f"Error deleting all files: {str(e)}")


@app.delete("/api/history/{file_id}")
def delete_history_file(file_id: int):
    """Soft delete a file from database and invalidate cached analysis. Runs in standard threadpool."""
    try:
        file_info = get_file_by_id(file_id)
        if not file_info:
            raise HTTPException(404, "File not found.")
            
        delete_file(file_id)
        
        # Remove local cache file if exists
        cache_path = get_cache_path(file_info['s3_key'])
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except Exception as e:
                print(f"Failed to remove cache file: {e}")
        
        # Invalidate combined session cache
        clear_calculation_caches()
        
        # Log deletion
        add_audit_log("File Deleted", file_info['filename'], f"Soft deleted file with ID {file_id} under role {file_info['role']}")
            
        return {"status": "success", "message": f"File '{file_info['filename']}' deleted successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"Error deleting file: {str(e)}")


@app.post("/api/history/replace/{file_id}")
async def replace_history_file(file_id: int, file: UploadFile = File(...)):
    """Replace an uploaded file with a new one in S3 and update database."""
    try:
        loop = asyncio.get_running_loop()
        file_info = await loop.run_in_executor(None, lambda: get_file_by_id(file_id))
        if not file_info:
            raise HTTPException(404, "File not found.")
            
        role = file_info['role']
        data = await file.read()
        
        # Remove old cache file
        old_cache_path = get_cache_path(file_info['s3_key'])
        if os.path.exists(old_cache_path):
            try:
                os.remove(old_cache_path)
            except Exception as e:
                print(f"Failed to remove old cache file: {e}")
        
        # 1. Upload new file to S3
        s3_res = await loop.run_in_executor(None, lambda: upload_file_to_s3(data, file.filename, role))
        
        # 2. Update record in DB
        updated = await loop.run_in_executor(
            None,
            lambda: replace_file(file_id, file.filename, s3_res["s3_key"], s3_res["s3_url"], s3_res["row_count"])
        )
        
        # Invalidate combined session cache
        clear_calculation_caches()
        
        # Log the file replacement
        await loop.run_in_executor(None, lambda: add_audit_log("File Replaced", file.filename, f"Replaced file with ID {file_id} under role {role}"))
            
        return {
            "status": "success",
            "file": {
                "id": updated["id"],
                "role": updated["role"],
                "filename": updated["filename"],
                "s3Key": updated["s3_key"],
                "s3Url": updated["s3_url"],
                "rowCount": updated["row_count"],
                "uploadedAt": str(updated["uploaded_at"]),
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"Error replacing file: {str(e)}")


# ── Analyze (SSE) ─────────────────────────────────────────────────────────────
@app.get("/api/analyze/{session_id}")
async def analyze(session_id: str):
    """
    SSE stream: emits progress events then a final 'result' event.
    Supports session-based runs or 'combined' run on S3 sheets.
    """
    if session_id == "combined":
        active_files = get_active_files()
        if not active_files:
            raise HTTPException(400, "No files uploaded yet.")
            
        cache_file = os.path.join(CACHE_DIR, "pipeline_result.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    result = pickle.load(f)
                sess = session_store.get_or_create_session("combined")
                sess.result = result
                
                async def cached_event_generator():
                    sanitized_res = sanitize_for_json(result)
                    yield {"data": json.dumps({"stage": "loading", "pct": 100, "message": "Loading from cache..."})}
                    await asyncio.sleep(0.05)
                    yield {"data": json.dumps({"stage": "result", "pct": 100, "result": sanitized_res}, default=str)}
                
                add_audit_log("Dashboard Fetched", "N/A", "Loaded dashboard values from disk cache")
                return EventSourceResponse(cached_event_generator())
            except Exception as e:
                print(f"Failed to read pipeline_result cache: {e}")

        async def event_generator():
            queue: asyncio.Queue = asyncio.Queue()
            
            async def emit(stage: str, pct: int, message: str):
                await queue.put({"stage": stage, "pct": pct, "message": message})
                await asyncio.sleep(0.05)
                
            async def run():
                try:
                    loop = asyncio.get_running_loop()
                    
                    def sync_on_progress(filename, role, current, total):
                        pct = 5 + int(((current - 1) / total) * 6)
                        msg = f"Loading {filename} ({role}) from S3 ({current}/{total})..."
                        loop.call_soon_threadsafe(
                            lambda: queue.put_nowait({"stage": "loading", "pct": pct, "message": msg})
                        )
                        
                    global cached_dfs
                    dfs = await loop.run_in_executor(None, lambda: load_combined_dfs(sync_on_progress))
                    cached_dfs = dfs
                    
                    if not dfs:
                        raise ValueError("No active sheets found or failed to load them.")
                        
                    sess = session_store.get_or_create_session("combined")
                    result = await run_pipeline(sess, emit, dfs_override=dfs)
                    session_store.set_result("combined", result)
                    
                    # Save cache file to disk
                    try:
                        with open(cache_file, "wb") as f:
                            pickle.dump(result, f)
                    except Exception as ce:
                        print(f"Failed to write cache: {ce}")
                        
                    # Log execution
                    await loop.run_in_executor(None, lambda: add_audit_log("Pipeline Run", "All Active Files", "Ran consolidated P2P audit pipeline"))
                    
                    await queue.put({"stage": "result", "pct": 100, "result": result})
                except Exception as exc:
                    await queue.put({"stage": "error", "pct": 0, "message": str(exc)})
                finally:
                    await queue.put(None)
                    
            task = asyncio.create_task(run())
            
            while True:
                item = await queue.get()
                if item is None:
                    break
                sanitized = sanitize_for_json(item)
                yield {"data": json.dumps(sanitized, default=str)}
                
            await task
            
        return EventSourceResponse(event_generator())
        
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")

    async def event_generator_legacy():
        queue: asyncio.Queue = asyncio.Queue()

        async def emit(stage: str, pct: int, message: str):
            await queue.put({"stage": stage, "pct": pct, "message": message})
            await asyncio.sleep(0.05)

        async def run():
            try:
                result = await run_pipeline(sess, emit)
                session_store.set_result(session_id, result)
                await queue.put({"stage": "result", "pct": 100, "result": result})
            except Exception as exc:
                await queue.put({"stage": "error", "pct": 0, "message": str(exc)})
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())

        while True:
            item = await queue.get()
            if item is None:
                break
            sanitized = sanitize_for_json(item)
            yield {"data": json.dumps(sanitized, default=str)}

        await task

    return EventSourceResponse(event_generator_legacy())


# ── AI Insights ───────────────────────────────────────────────────────────────
@app.post("/api/insights/{section}")
def insights(section: str, body: dict):
    """
    Returns AI-generated narrative for a section.
    Body: {kpis: {...}, top_risks?: [...]}
    """
    kpis = body.get("kpis", {})
    top_risks = body.get("top_risks", [])

    if section == "executive":
        text = generate_executive_summary(kpis, top_risks)
    else:
        text = generate_section_insight(section, kpis)

    return {"section": section, "narrative": text}


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── Get stored result ─────────────────────────────────────────────────────────
@app.get("/api/result/{session_id}")
def get_result(session_id: str):
    if session_id == "combined":
        cache_file = os.path.join(CACHE_DIR, "pipeline_result.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "rb") as f:
                    result = pickle.load(f)
                sess = session_store.get_or_create_session("combined")
                sess.result = result
                add_audit_log("Dashboard Fetched", "N/A", "Loaded dashboard values from disk cache")
                return sanitize_for_json(result)
            except Exception as e:
                print(f"Failed to read pipeline_result cache: {e}")

        sess = session_store.get_session("combined")
        if sess is None or sess.result is None:
            active_files = get_active_files()
            if active_files:
                raise HTTPException(404, "Result not yet computed")
            else:
                raise HTTPException(404, "No files uploaded")
        add_audit_log("Dashboard Fetched", "N/A", "Loaded dashboard values from memory")
        return sanitize_for_json(sess.result)
        
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(404, "Session not found.")
    if sess.result is None:
        raise HTTPException(404, "Result not yet computed.")
    return sanitize_for_json(sess.result)


def get_cached_or_compute(cache_name: str, compute_fn):
    cache_path = os.path.join(CACHE_DIR, f"{cache_name}.pkl")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Failed to read disk cache for {cache_name}: {e}")
            
    res = compute_fn()
    sanitized = sanitize_for_json(res)
    
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(sanitized, f)
    except Exception as ce:
        print(f"Failed to write disk cache for {cache_name}: {ce}")
        
    return sanitized

# ── Price Variance Endpoints ───────────────────────────────────────────────
@app.get("/api/analysis/price-variance-same")
async def get_price_variance_same():
    global cached_price_variance_same
    if cached_price_variance_same is not None:
        return cached_price_variance_same
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.price_variance_new import run_variance_analysis
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("price_variance_same", lambda: run_variance_analysis(dfs, "same")))
        cached_price_variance_same = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing same-vendor price variance: {str(e)}")

@app.get("/api/analysis/price-variance-cross")
async def get_price_variance_cross():
    global cached_price_variance_cross
    if cached_price_variance_cross is not None:
        return cached_price_variance_cross
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.price_variance_new import run_variance_analysis
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("price_variance_cross", lambda: run_variance_analysis(dfs, "cross")))
        cached_price_variance_cross = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing cross-vendor price variance: {str(e)}")

@app.get("/api/analysis/payment-aging-domestic")
async def get_payment_aging_domestic():
    global cached_aging_domestic
    if cached_aging_domestic is not None:
        return cached_aging_domestic
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.payment_aging_domestic import run_payment_aging_domestic
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("aging_domestic", lambda: run_payment_aging_domestic(dfs)))
        cached_aging_domestic = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing payment aging (domestic): {str(e)}")

@app.get("/api/analysis/payment-aging-foreign")
async def get_payment_aging_foreign():
    global cached_aging_foreign
    if cached_aging_foreign is not None:
        return cached_aging_foreign
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.payment_aging_foreign import run_payment_aging_foreign
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("aging_foreign", lambda: run_payment_aging_foreign(dfs)))
        cached_aging_foreign = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing payment aging (foreign): {str(e)}")

@app.get("/api/analysis/payment-aging-related")
async def get_payment_aging_related():
    global cached_aging_related
    if cached_aging_related is not None:
        return cached_aging_related
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.payment_aging_related import run_payment_aging_related
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("aging_related", lambda: run_payment_aging_related(dfs)))
        cached_aging_related = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing payment aging (related): {str(e)}")

@app.get("/api/analysis/payment-aging-msme")
async def get_payment_aging_msme():
    global cached_aging_msme
    if cached_aging_msme is not None:
        return cached_aging_msme
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.payment_aging_msme import run_payment_aging_msme
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("aging_msme", lambda: run_payment_aging_msme(dfs)))
        cached_aging_msme = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing payment aging (msme): {str(e)}")

@app.get("/api/analysis/vendor-master-new")
async def get_vendor_master_new():
    global cached_vendor_master_new
    if cached_vendor_master_new is not None:
        return cached_vendor_master_new
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.vendor_master_new import run_vendor_master_new
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("vendor_master_new", lambda: run_vendor_master_new(dfs)))
        cached_vendor_master_new = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing vendor master new: {str(e)}")

@app.get("/api/analysis/three-way-matching")
async def get_three_way_matching():
    global cached_three_way_matching
    if cached_three_way_matching is not None:
        return cached_three_way_matching
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        from app.analysis.three_way_matching import run_three_way_matching
        res = await loop.run_in_executor(None, lambda: get_cached_or_compute("three_way_matching", lambda: run_three_way_matching(dfs)))
        cached_three_way_matching = res
        return res
    except Exception as e:
        raise HTTPException(500, f"Error computing 3-way matching: {str(e)}")
@app.get("/api/logs")
def get_logs(limit: int = 100):
    """
    Fetch the list of system action and audit logs.
    """
    try:
        logs = get_audit_logs()
        return logs
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/audit-trace/search")
async def audit_trace_search(query: str):
    """
    Real-time cross-reference search across the 9 raw source DataFrames.
    Supports comma-separated multi-value queries (e.g. multiple POs, dates, GRNs, Invoices).
    Returns matched rows grouped by file role.
    """
    if not query:
        return {}
        
    try:
        loop = asyncio.get_running_loop()
        dfs = await loop.run_in_executor(None, get_cached_dfs_or_load)
        
        def do_search():
            results = {}
            query_str = str(query).strip()
            if not query_str:
                return {}
                
            # Split comma-separated tokens if present
            raw_tokens = [t.strip() for t in query_str.split(",") if t.strip()]
            tokens = [t for t in raw_tokens if t.lower() not in ("—", "none", "nan", "null", "nat", "")]
            if not tokens:
                return {}

            for role, df in dfs.items():
                if df is None or df.empty:
                    continue
                    
                combined_mask = pd.Series(False, index=df.index)

                # Pre-identify date columns in this df to avoid running pd.to_datetime on arbitrary string columns
                date_cols = set()
                for col in df.columns:
                    col_str = str(col).lower()
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        date_cols.add(col)
                    elif any(k in col_str for k in ("date", "dt", "time", "created", "updated", "period", "posting")):
                        date_cols.add(col)

                for token_str in tokens:
                    token_mask = pd.Series(False, index=df.index)

                    # 1. Check numeric token
                    token_float = None
                    try:
                        token_float = float(token_str)
                    except ValueError:
                        pass

                    # 2. Check date token
                    token_dt = None
                    token_date_str_variants = set([token_str])
                    if any(c in token_str for c in ("/", "-", ".")) and len(token_str) >= 6:
                        try:
                            dt_cand = pd.to_datetime(token_str, dayfirst=True, errors="coerce")
                            if not pd.isna(dt_cand) and 1990 <= dt_cand.year <= 2100:
                                token_dt = dt_cand
                                d = dt_cand.day
                                m = dt_cand.month
                                y = dt_cand.year
                                yy = str(y)[-2:]
                                token_date_str_variants.add(f"{d:02d}/{m:02d}/{y}")
                                token_date_str_variants.add(f"{d:02d}.{m:02d}.{y}")
                                token_date_str_variants.add(f"{d:02d}-{m:02d}-{y}")
                                token_date_str_variants.add(f"{y}-{m:02d}-{d:02d}")
                                token_date_str_variants.add(f"{d:02d}/{m:02d}/{yy}")
                                token_date_str_variants.add(f"{d:02d}.{m:02d}.{yy}")
                                token_date_str_variants.add(f"{d}/{m}/{y}")
                                token_date_str_variants.add(f"{d}.{m}.{y}")
                        except Exception:
                            pass

                    # Check each column
                    for col in df.columns:
                        col_series = df[col]
                        
                        # Numeric column check
                        if pd.api.types.is_numeric_dtype(col_series):
                            if token_float is not None:
                                try:
                                    num_mask = (col_series == token_float) | (col_series.round(2) == round(token_float, 2))
                                    token_mask = token_mask | num_mask
                                except Exception:
                                    pass
                        # String / Object column check
                        elif pd.api.types.is_object_dtype(col_series) or pd.api.types.is_string_dtype(col_series):
                            try:
                                str_col = col_series.astype(str)
                                str_mask = pd.Series(False, index=df.index)
                                for var in token_date_str_variants:
                                    str_mask = str_mask | str_col.str.contains(var, case=False, na=False, regex=False)
                                token_mask = token_mask | str_mask
                            except Exception:
                                pass
                        # Datetime column check
                        elif pd.api.types.is_datetime64_any_dtype(col_series):
                            if token_dt is not None:
                                try:
                                    dt_mask = col_series.dt.date == token_dt.date()
                                    token_mask = token_mask | dt_mask
                                except Exception:
                                    pass
                        else:
                            try:
                                str_col = col_series.astype(str)
                                str_mask = str_col.str.contains(token_str, case=False, na=False, regex=False)
                                token_mask = token_mask | str_mask
                            except Exception:
                                pass

                        # Additional date matching for known date columns
                        if token_dt is not None and col in date_cols and not pd.api.types.is_datetime64_any_dtype(col_series):
                            try:
                                col_dt = pd.to_datetime(col_series, dayfirst=True, errors="coerce")
                                dt_mask = col_dt.dt.date == token_dt.date()
                                token_mask = token_mask | dt_mask.fillna(False)
                            except Exception:
                                pass

                    combined_mask = combined_mask | token_mask

                matched_df = df[combined_mask]
                if not matched_df.empty:
                    sample_df = matched_df.head(50)
                    records = sample_df.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
                    results[role] = sanitize_for_json(records)
                    
            return results
            
        search_results = await loop.run_in_executor(None, do_search)
        return search_results
    except Exception as e:
        raise HTTPException(500, f"Error searching raw source files: {str(e)}")


@app.get("/api/user-profile")
def get_profile():
    try:
        from app.db import get_user_profile
        return get_user_profile()
    except Exception as e:
        raise HTTPException(500, f"Error fetching profile: {str(e)}")


@app.post("/api/user-profile")
async def update_profile(
    name: str = Form(...),
    mobile_number: str = Form(...),
    email: str = Form(...),
    profile_pic: Optional[UploadFile] = File(None)
):
    try:
        from app.db import update_user_profile
        from app.s3 import upload_profile_pic_to_s3
        
        pic_url = None
        if profile_pic and profile_pic.filename:
            data = await profile_pic.read()
            pic_url = upload_profile_pic_to_s3(data, profile_pic.filename)
            
        profile = update_user_profile(name, pic_url, mobile_number, email)
        return profile
    except Exception as e:
        raise HTTPException(500, f"Error updating profile: {str(e)}")

