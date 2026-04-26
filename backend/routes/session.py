"""
routes/session.py — All Session Endpoints
==========================================
"""

import io
import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from schemas import (
    StartSessionRequest, StartSessionResponse,
    MessageRequest, MessageResponse,
    EvaluateRequest, EvaluateResponse,
)
import session_store
from agents import interviewer, evaluator
from file_parser import extract_text

router = APIRouter(prefix="/session", tags=["session"])


# ─── Deepgram TTS client — initialised once at startup ───────────────────────
from deepgram import DeepgramClient, SpeakOptions as _SpeakOptions

_DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
_deepgram = DeepgramClient(api_key=_DEEPGRAM_API_KEY) if _DEEPGRAM_API_KEY else None

if _deepgram:
    print("[Deepgram] TTS client ready.")
else:
    print("[Deepgram] WARNING: DEEPGRAM_API_KEY not set — /session/tts will fail.")


class TTSRequest(BaseModel):
    text: str
    voice: str = "aura-orion-en"   # swap to "aura-asteria-en" for female


# ─── Session Endpoints ────────────────────────────────────────────────────────

@router.post("/start", response_model=StartSessionResponse)
async def start_session(body: StartSessionRequest):
    if not body.source_text or len(body.source_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="source_text is too short — paste a real abstract.")

    session = session_store.create_session(
        source_text=body.source_text.strip(),
        persona=body.persona,
    )
    first_question = interviewer.get_first_question(
    body.source_text.strip(),
    persona=session.persona,
    )
    session_store.append_turn(session.session_id, role="assistant", content=first_question)

    return StartSessionResponse(
        session_id=session.session_id,
        first_question=first_question,
    )


@router.post("/start-from-file", response_model=StartSessionResponse)
async def start_session_from_file(file: UploadFile = File(...)):
    source_text = await extract_text(file)

    if len(source_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="Not enough text could be extracted from the file.")

    session = session_store.create_session(source_text=source_text.strip())
    first_question = interviewer.get_first_question(source_text.strip())
    session_store.append_turn(session.session_id, role="assistant", content=first_question)

    return StartSessionResponse(
        session_id=session.session_id,
        first_question=first_question,
    )


@router.post("/message", response_model=MessageResponse)
async def send_message(body: MessageRequest):
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{body.session_id}' not found.")

    if session.is_complete:
        raise HTTPException(status_code=400, detail="This interview is already complete. Call /evaluate to get your report.")

    if not body.user_message or len(body.user_message.strip()) == 0:
        raise HTTPException(status_code=422, detail="user_message cannot be empty.")

    session_store.append_turn(body.session_id, role="user", content=body.user_message.strip())
    session = session_store.get_session(body.session_id)
    interview_done = interviewer.is_interview_complete(session.turn_count)

    agent_reply = interviewer.get_next_question(
        source_text=session.source_text,
        transcript=[e.dict() for e in session.transcript],
        turn_count=session.turn_count,
        persona=session.persona,
    )

    session_store.append_turn(body.session_id, role="assistant", content=agent_reply)

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
    deleted = session_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"deleted": session_id}


# ─── TTS Endpoint ─────────────────────────────────────────────────────────────
# Accepts text, calls Deepgram, returns raw WAV audio bytes.
# The browser fetches this, creates a Blob URL, and plays it with Audio().

@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    """
    Convert text to speech using Deepgram and return audio/wav bytes.
    Called by the frontend after every agent_reply.
    """
    if not _deepgram:
        raise HTTPException(status_code=500, detail="DEEPGRAM_API_KEY is not configured.")

    if not body.text or not body.text.strip():
        raise HTTPException(status_code=422, detail="text cannot be empty.")

    options = _SpeakOptions(model=body.voice)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        _deepgram.speak.v("1").save(tmp_path, {"text": body.text.strip()}, options)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Cache-Control": "no-cache"},
    )


# ─── Whisper model — loaded once at startup ───────────────────────────────────

import ssl
import whisper as _whisper

_orig_https = ssl._create_default_https_context
ssl._create_default_https_context = ssl._create_unverified_context

try:
    _whisper_model = _whisper.load_model("base")
    print("[Whisper] Model loaded successfully at startup.")
except Exception as _e:
    _whisper_model = None
    print(f"[Whisper] WARNING: Could not load model at startup: {_e}")

ssl._create_default_https_context = _orig_https


# ─── Transcription Endpoint ───────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Accept a browser audio recording (webm), transcribe with Whisper,
    return { "text": "..." }.
    """
    if _whisper_model is None:
        raise HTTPException(
            status_code=500,
            detail="Whisper model failed to load at startup. Check server logs."
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Uploaded audio file is empty.")

    suffix = os.path.splitext(file.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = _whisper_model.transcribe(tmp_path)
        text = result["text"].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"text": text}