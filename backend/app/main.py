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
from app.db import init_db, add_uploaded_file, get_active_files, delete_file, replace_file, get_file_by_id
from app.s3 import upload_file_to_s3, download_file_from_s3

# Initialize the database on startup
init_db()

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


def load_combined_dfs(on_progress=None) -> dict[str, pd.DataFrame]:
    """
    Load all active S3 files, group them by role,
    and concatenate them into a combined dictionary of DataFrames.
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
    
    for idx, (role, fi) in enumerate(flat_files):
        if on_progress:
            try:
                on_progress(fi['filename'], role, idx + 1, total_files)
            except Exception:
                pass
        try:
            data = download_file_from_s3(fi['s3_key'])
            df = load_file(io.BytesIO(data), fi['filename'])
            if role not in dfs_lists:
                dfs_lists[role] = []
            dfs_lists[role].append(df)
        except Exception as e:
            print(f"Error loading file {fi['filename']} for role {role}: {e}")
            
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
    Upload files, save to S3, record in database,
    and invalidate the combined analysis cache.
    """
    if len(files) != len(roles):
        raise HTTPException(400, "files and roles must have equal length.")

    valid_roles = set(FILE_ROLES.keys())
    for r in roles:
        if r not in valid_roles:
            raise HTTPException(400, f"Unknown role '{r}'. Valid: {list(valid_roles)}")

    # Invalidate combined result cache
    combined_sess = session_store.get_session("combined")
    if combined_sess:
        combined_sess.result = None

    file_info = []
    for uf, role in zip(files, roles):
        data = await uf.read()
        try:
            # 1. Upload to S3
            s3_res = upload_file_to_s3(data, uf.filename, role)
            # 2. Add to Database
            db_res = add_uploaded_file(role, uf.filename, s3_res["s3_key"], s3_res["s3_url"], s3_res["row_count"])
            file_info.append({
                "id": db_res["id"],
                "role": db_res["role"],
                "filename": db_res["filename"],
                "s3Key": db_res["s3_key"],
                "s3Url": db_res["s3_url"],
                "rowCount": db_res["row_count"],
                "uploadedAt": str(db_res["uploaded_at"]),
            })
        except Exception as exc:
            raise HTTPException(422, f"Cannot process/upload '{uf.filename}': {exc}")

    return {"session_id": "combined", "files": file_info}


# ── Audit History Management ──────────────────────────────────────────────────
@app.get("/api/history")
async def list_history():
    """List all active uploaded files."""
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


@app.delete("/api/history/{file_id}")
async def delete_history_file(file_id: int):
    """Soft delete a file from database and invalidate cached analysis."""
    try:
        file_info = get_file_by_id(file_id)
        if not file_info:
            raise HTTPException(404, "File not found.")
            
        delete_file(file_id)
        
        # Invalidate combined session cache
        sess = session_store.get_session("combined")
        if sess:
            sess.result = None
            
        return {"status": "success", "message": f"File '{file_info['filename']}' deleted successfully."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(500, f"Error deleting file: {str(e)}")


@app.post("/api/history/replace/{file_id}")
async def replace_history_file(file_id: int, file: UploadFile = File(...)):
    """Replace an uploaded file with a new one in S3 and update database."""
    try:
        file_info = get_file_by_id(file_id)
        if not file_info:
            raise HTTPException(404, "File not found.")
            
        role = file_info['role']
        data = await file.read()
        
        # 1. Upload new file to S3
        s3_res = upload_file_to_s3(data, file.filename, role)
        
        # 2. Update record in DB
        updated = replace_file(file_id, file.filename, s3_res["s3_key"], s3_res["s3_url"], s3_res["row_count"])
        
        # Invalidate combined session cache
        sess = session_store.get_session("combined")
        if sess:
            sess.result = None
            
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
            
        async def event_generator():
            queue: asyncio.Queue = asyncio.Queue()
            
            async def emit(stage: str, pct: int, message: str):
                await queue.put({"stage": stage, "pct": pct, "message": message})
                
            async def run():
                try:
                    loop = asyncio.get_running_loop()
                    
                    def sync_on_progress(filename, role, current, total):
                        pct = 5 + int(((current - 1) / total) * 6)
                        msg = f"Loading {filename} ({role}) from S3 ({current}/{total})..."
                        loop.call_soon_threadsafe(
                            lambda: queue.put_nowait({"stage": "loading", "pct": pct, "message": msg})
                        )
                        
                    dfs = await loop.run_in_executor(None, lambda: load_combined_dfs(sync_on_progress))
                    
                    if not dfs:
                        raise ValueError("No active sheets found or failed to load them.")
                        
                    sess = session_store.get_or_create_session("combined")
                    result = await run_pipeline(sess, emit, dfs_override=dfs)
                    session_store.set_result("combined", result)
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
async def insights(section: str, body: dict):
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
async def health():
    return {"status": "ok"}


# ── Get stored result ─────────────────────────────────────────────────────────
@app.get("/api/result/{session_id}")
async def get_result(session_id: str):
    if session_id == "combined":
        sess = session_store.get_session("combined")
        if sess is None or sess.result is None:
            active_files = get_active_files()
            if active_files:
                raise HTTPException(404, "Result not yet computed")
            else:
                raise HTTPException(404, "No files uploaded")
        return sanitize_for_json(sess.result)
        
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(404, "Session not found.")
    if sess.result is None:
        raise HTTPException(404, "Result not yet computed.")
    return sanitize_for_json(sess.result)
