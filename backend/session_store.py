"""
session_store.py — In-Memory Session Storage
=============================================
Simple dict-based store. No database needed for MVP.
Sessions live as long as the server process is running.
"""

import uuid
from typing import Dict, Optional
from schemas import Session, TranscriptEntry


# The global store — keyed by session_id string
_sessions: Dict[str, Session] = {}


def create_session(source_text: str, persona: str = "exec") -> Session:
    session_id = str(uuid.uuid4())
    session = Session(
        session_id=session_id,
        source_text=source_text,
        persona=persona,
    )
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[Session]:
    return _sessions.get(session_id)


def append_turn(session_id: str, role: str, content: str) -> Session:
    """Append a single message to a session's transcript and increment turn count."""
    session = _sessions[session_id]
    session.transcript.append(TranscriptEntry(role=role, content=content))
    if role == "user":
        session.turn_count += 1
    return session


def mark_complete(session_id: str) -> Session:
    session = _sessions[session_id]
    session.is_complete = True
    return session


def delete_session(session_id: str) -> bool:
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def all_session_ids() -> list:
    """Debug helper — not exposed in prod routes."""
    return list(_sessions.keys())
