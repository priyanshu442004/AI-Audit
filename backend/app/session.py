"""In-memory session storage: uploaded file bytes keyed by session_id + role."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class UploadedFile:
    role: str
    filename: str
    data: bytes


@dataclass
class Session:
    session_id: str
    files: Dict[str, UploadedFile] = field(default_factory=dict)
    result: Optional[dict] = None


_store: Dict[str, Session] = {}


def new_session() -> Session:
    sid = str(uuid.uuid4())
    s = Session(session_id=sid)
    _store[sid] = s
    return s


def get_session(session_id: str) -> Optional[Session]:
    return _store.get(session_id)


def add_file(session_id: str, role: str, filename: str, data: bytes) -> None:
    s = _store.get(session_id)
    if s is None:
        raise KeyError(f"Session '{session_id}' not found.")
    s.files[role] = UploadedFile(role=role, filename=filename, data=data)


def set_result(session_id: str, result: dict) -> None:
    s = _store.get(session_id)
    if s:
        s.result = result


def get_or_create_session(session_id: str) -> Session:
    if session_id not in _store:
        _store[session_id] = Session(session_id=session_id)
    return _store[session_id]

