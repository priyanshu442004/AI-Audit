"""FastAPI application — IKIO P2P Audit Dashboard API."""

from __future__ import annotations

import asyncio
import io
import json
import math
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

import app.session as session_store
from app.loaders import load_file
from app.pipeline import run_pipeline
from app.insights import generate_section_insight, generate_executive_summary
from app.config import FILE_ROLES


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
    Upload up to 6 files tagged by role.
    roles and files must be parallel lists.
    Returns {session_id, files: [{role, filename, rows, detected_columns}]}.
    """
    if len(files) != len(roles):
        raise HTTPException(400, "files and roles must have equal length.")

    valid_roles = set(FILE_ROLES.keys())
    for r in roles:
        if r not in valid_roles:
            raise HTTPException(400, f"Unknown role '{r}'. Valid: {list(valid_roles)}")

    sess = session_store.new_session()

    file_info = []
    for uf, role in zip(files, roles):
        data = await uf.read()
        try:
            df = load_file(io.BytesIO(data), uf.filename)
        except Exception as exc:
            raise HTTPException(422, f"Cannot read '{uf.filename}': {exc}")

        session_store.add_file(sess.session_id, role, uf.filename, data)

        from app.cleaning import detect_columns
        detected = list(detect_columns(df).keys())

        file_info.append({
            "role":              role,
            "filename":          uf.filename,
            "rows":              len(df),
            "detected_columns":  detected,
        })

    return {"session_id": sess.session_id, "files": file_info}


# ── Analyze (SSE) ─────────────────────────────────────────────────────────────
@app.get("/api/analyze/{session_id}")
async def analyze(session_id: str):
    """
    SSE stream: emits progress events then a final 'result' event.

    Each progress event: data = JSON {stage, pct, message}
    Final event:        data = JSON {stage:"result", result:{...}}
    """
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")

    async def event_generator():
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
                await queue.put(None)  # sentinel

        task = asyncio.create_task(run())

        while True:
            item = await queue.get()
            if item is None:
                break
            sanitized = sanitize_for_json(item)
            yield {"data": json.dumps(sanitized, default=str)}

        await task

    return EventSourceResponse(event_generator())


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
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(404, "Session not found.")
    if sess.result is None:
        raise HTTPException(404, "Result not yet computed.")
    return sanitize_for_json(sess.result)
