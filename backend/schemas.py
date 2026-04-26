"""
schemas.py — Shared API Contract
=================================
THIS FILE IS THE SOURCE OF TRUTH.
Both backend and frontend (types.ts) must match these shapes exactly.
Do NOT rename fields without updating types.ts and notifying Pair B.
"""

from pydantic import BaseModel
from typing import List, Optional


# ─── Request Bodies ────────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    source_text: str           # The abstract / presentation text being discussed
    persona: str = "exec"      # Future-proofed; only "exec" for MVP


class MessageRequest(BaseModel):
    session_id: str
    user_message: str          # Text content (typed OR transcribed from speech)


class EvaluateRequest(BaseModel):
    session_id: str


# ─── Response Bodies ───────────────────────────────────────────────────────────

class StartSessionResponse(BaseModel):
    session_id: str
    first_question: str        # First question from the interviewer agent


class MessageResponse(BaseModel):
    session_id: str
    agent_reply: str           # Next question or closing remark from agent
    turn_number: int           # How many turns have elapsed
    interview_complete: bool   # True when agent has asked enough questions


class JargonTerm(BaseModel):
    term: str
    suggestion: str            # Plain-English alternative


class EvaluateResponse(BaseModel):
    clarity: int               # 1–10
    tone: int                  # 1–10
    jargon_score: int          # 1–10 (10 = no jargon, 1 = jargon-heavy)
    jargon_terms: List[JargonTerm]
    summary: str               # 2–3 sentence overall summary
    top_fix: str               # Single most important improvement


# ─── Internal Session Shape ────────────────────────────────────────────────────

class TranscriptEntry(BaseModel):
    role: str                  # "user" or "assistant"
    content: str


class Session(BaseModel):
    session_id: str
    source_text: str
    transcript: List[TranscriptEntry] = []
    persona: str = "exec"
    turn_count: int = 0
    is_complete: bool = False


# ─── Misc ──────────────────────────────────────────────────────────────────────

class SampleText(BaseModel):
    id: str
    title: str
    preview: str               # First ~80 chars shown in the UI button
    full_text: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
