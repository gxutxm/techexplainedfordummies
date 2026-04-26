"""
routes/session.py — All Session Endpoints
==========================================
"""

from fastapi import APIRouter, HTTPException
from schemas import (
    StartSessionRequest, StartSessionResponse,
    MessageRequest, MessageResponse,
    EvaluateRequest, EvaluateResponse,
)
import session_store
from agents import interviewer, evaluator

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(body: StartSessionRequest):
    """
    Create a new interview session.
    Accepts the source text (abstract/presentation).
    Returns session_id + the interviewer's first question.
    """
    if not body.source_text or len(body.source_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="source_text is too short — paste a real abstract.")

    # Create session in store
    session = session_store.create_session(
        source_text=body.source_text.strip(),
        persona=body.persona,
    )

    # Get first question from interviewer agent
    first_question = interviewer.get_first_question(body.source_text.strip())

    # Save agent's first message to transcript
    session_store.append_turn(session.session_id, role="assistant", content=first_question)

    return StartSessionResponse(
        session_id=session.session_id,
        first_question=first_question,
    )


@router.post("/message", response_model=MessageResponse)
async def send_message(body: MessageRequest):
    """
    Send the user's reply and get the next interviewer question.
    
    This endpoint is speech-agnostic — the caller passes transcribed text
    if using voice input. The backend doesn't care how the text was captured.
    """
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    if session.is_complete:
        raise HTTPException(status_code=400, detail="This interview is already complete. Call /evaluate to get your report.")

    if not body.user_message or len(body.user_message.strip()) == 0:
        raise HTTPException(status_code=422, detail="user_message cannot be empty.")

    # Save user's reply
    session_store.append_turn(body.session_id, role="user", content=body.user_message.strip())

    # Reload session to get updated transcript + turn count
    session = session_store.get_session(body.session_id)

    # Check if interview should end after this turn
    interview_done = interviewer.is_interview_complete(session.turn_count)

    # Get next agent response (closing remark if done, next question if not)
    agent_reply = interviewer.get_next_question(
        source_text=session.source_text,
        transcript=[e.dict() for e in session.transcript],
        turn_count=session.turn_count,
    )

    # Save agent reply
    session_store.append_turn(body.session_id, role="assistant", content=agent_reply)

    # Mark complete if we've hit the turn limit
    if interview_done:
        session_store.mark_complete(body.session_id)

    return MessageResponse(
        session_id=body.session_id,
        agent_reply=agent_reply,
        turn_number=session.turn_count,
        interview_complete=interview_done,
    )


@router.post("/{session_id}/evaluate", response_model=EvaluateResponse)
async def evaluate_session(session_id: str):
    """
    Evaluate the full interview transcript.
    Returns scored feedback report.
    
    Can be called at any point, but ideally after interview_complete=True.
    """
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    if len(session.transcript) < 2:
        raise HTTPException(status_code=400, detail="Not enough transcript to evaluate. Complete at least one exchange first.")

    result = evaluator.evaluate_transcript(
        source_text=session.source_text,
        transcript=session.transcript,
    )

    return result


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Optional: clean up a session."""
    deleted = session_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"deleted": session_id}
