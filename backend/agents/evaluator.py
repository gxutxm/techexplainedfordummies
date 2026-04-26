"""
agents/evaluator.py — Evaluator Agent
======================================
Owned by: Pair B / Person 1

Reads the full interview transcript and scores the presenter on three
dimensions: clarity, tone, and jargon usage. Returns structured JSON
feedback that the React report screen renders.

Behavior contract:
  - Calls Claude with temperature=0 for deterministic JSON output.
  - On malformed JSON, retries once with a stricter prompt.
  - On second failure, raises HTTPException(502) — the route surfaces it
    cleanly instead of returning fake/fallback scores.

Output shape (must match schemas.EvaluateResponse exactly):
{
  "clarity":      int 1-10,
  "tone":         int 1-10,
  "jargon_score": int 1-10,
  "jargon_terms": [{ "term": str, "suggestion": str }],
  "summary":      str  (2-3 sentences),
  "top_fix":      str  (single most impactful improvement)
}
"""

import json
import logging
import re

from fastapi import HTTPException

import llm_client
from config import EVALUATOR_MODEL, MAX_TOKENS
from schemas import EvaluateResponse, JargonTerm

log = logging.getLogger(__name__)


# ─── System Prompt ────────────────────────────────────────────────────────────

EVALUATOR_SYSTEM_PROMPT = """You are an expert communication coach evaluating how well someone explained a technical topic to a non-technical executive audience.

You will receive:
1. The original source text (abstract or presentation) the interviewee was asked about
2. A full transcript of the interview between an executive (assistant) and a presenter (user)

Your job is to evaluate ONLY the PRESENTER'S responses (the "user" turns) on three dimensions.

═══════════════════════════════════════════════════════════════
SCORING RUBRIC (each 1–10)
═══════════════════════════════════════════════════════════════

CLARITY — How easy was it to follow the presenter's answers?
  1–3: Confusing, jumped between ideas, assumed knowledge the executive didn't have
  4–6: Followable but had unclear moments or missing context
  7–8: Clear structure, used analogies or concrete examples, built ideas progressively
  9–10: Exceptionally clear; a smart non-expert would walk away genuinely understanding

TONE — Was the presenter's tone right for an executive audience?
  1–3: Condescending, dismissive, defensive, or overly academic
  4–6: Neutral but flat; didn't engage the executive
  7–8: Confident, respectful, conversational
  9–10: Warm, engaging, made the executive feel smart for asking

JARGON_SCORE — How well did the presenter avoid or explain technical jargon? HIGHER = LESS JARGON (better)
  1–3: Heavy unexplained jargon throughout
  4–6: Some jargon used but inconsistently explained
  7–8: Mostly plain language; jargon explained when used
  9–10: Almost no unexplained jargon; technical terms always defined in context

═══════════════════════════════════════════════════════════════
JARGON_TERMS
═══════════════════════════════════════════════════════════════
Identify up to 5 specific phrases the presenter used WITHOUT adequate explanation
that an executive would not understand. For each, provide a plain-English rewrite.

If the presenter explained their jargon well throughout, return an empty list — do
not invent problems that weren't there.

═══════════════════════════════════════════════════════════════
SUMMARY & TOP_FIX
═══════════════════════════════════════════════════════════════
SUMMARY: 2–3 sentences addressed to the presenter as "you". Honest but constructive.
TOP_FIX: The single most impactful change they could make, one sentence.

═══════════════════════════════════════════════════════════════
OUTPUT FORMAT — CRITICAL
═══════════════════════════════════════════════════════════════
Return ONLY a valid JSON object. No markdown. No code fences. No preamble.
No explanation. Just the JSON.

Match this exact shape:

{
  "clarity": <int 1-10>,
  "tone": <int 1-10>,
  "jargon_score": <int 1-10>,
  "jargon_terms": [
    {"term": "<exact phrase the presenter said>", "suggestion": "<plain-language rewrite>"}
  ],
  "summary": "<2-3 sentences, plain prose, addressed to the presenter as 'you'>",
  "top_fix": "<single most impactful change, one sentence>"
}
"""


# Used only on the retry attempt — appended to the user message
_RETRY_SUFFIX = (
    "\n\n[CRITICAL] Your previous response was not valid JSON. "
    "Return ONLY a JSON object with NO other text, NO markdown fences, "
    "NO explanation, and NO preamble. Just the raw JSON."
)


# ─── Public API ───────────────────────────────────────────────────────────────

def evaluate_transcript(source_text: str, transcript: list) -> EvaluateResponse:
    """
    Evaluate the full interview transcript and return structured feedback.

    Calls Claude up to twice — once normally, once with a stricter retry prompt
    if the first response wasn't parseable JSON. Raises HTTPException(502) if
    both attempts fail rather than returning meaningless fallback scores.
    """
    transcript_text = _format_transcript(transcript)
    user_message = _build_user_message(source_text, transcript_text)

    # ── First attempt ───────────────────────────────
    raw = _call_claude(user_message)
    parsed = _try_parse(raw)
    if parsed is not None:
        return parsed

    log.warning("Evaluator: first response was not valid JSON, retrying once. Raw head: %r", raw[:200])

    # ── Retry with stricter prompt ──────────────────
    raw_retry = _call_claude(user_message + _RETRY_SUFFIX)
    parsed_retry = _try_parse(raw_retry)
    if parsed_retry is not None:
        return parsed_retry

    log.error("Evaluator: failed twice. Last raw head: %r", raw_retry[:300])
    raise HTTPException(
        status_code=502,
        detail="The evaluator returned malformed JSON twice. Please try again in a moment.",
    )


# ─── Internals ────────────────────────────────────────────────────────────────

def _build_user_message(source_text: str, transcript_text: str) -> str:
    return (
        f"SOURCE TEXT (what the presenter was asked about):\n"
        f"---\n{source_text}\n---\n\n"
        f"INTERVIEW TRANSCRIPT:\n"
        f"---\n{transcript_text}\n---\n\n"
        f"Evaluate the presenter's communication and return ONLY the JSON object."
    )


def _call_claude(user_message: str) -> str:
    """
    Single call to the LLM client. Uses temperature=0 for deterministic JSON.
    Trusts llm_client to route to whichever provider config.py specifies.
    """
    return llm_client.chat(
        system=EVALUATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        model=EVALUATOR_MODEL,
        max_tokens=MAX_TOKENS["evaluator"],
        temperature=0.0,
    )


def _try_parse(raw: str) -> EvaluateResponse | None:
    """
    Try to coerce Claude's response into an EvaluateResponse. Returns None on
    failure rather than raising — caller decides what to do (retry or 502).
    """
    if not raw:
        return None

    extracted = _extract_json(raw)
    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as e:
        log.debug("Evaluator JSON decode failed: %s. Extracted: %r", e, extracted[:300])
        return None

    try:
        return EvaluateResponse(
            clarity=_clamp_score(data["clarity"]),
            tone=_clamp_score(data["tone"]),
            jargon_score=_clamp_score(data["jargon_score"]),
            jargon_terms=[
                JargonTerm(term=str(j["term"]).strip(), suggestion=str(j["suggestion"]).strip())
                for j in data.get("jargon_terms", [])
                if isinstance(j, dict) and j.get("term") and j.get("suggestion")
            ][:5],  # Cap at 5 to keep the report focused
            summary=str(data["summary"]).strip(),
            top_fix=str(data["top_fix"]).strip(),
        )
    except (KeyError, TypeError, ValueError) as e:
        log.debug("Evaluator schema validation failed: %s. Data: %r", e, data)
        return None


def _extract_json(text: str) -> str:
    """
    Robust JSON extraction. Handles three common Claude failure modes:
      1. Markdown code fences:        ```json\n{...}\n```
      2. Preamble text:               "Here's your evaluation: {...}"
      3. Trailing text after JSON:    "{...} Hope this helps!"

    Strategy: strip fences, then take everything between the first '{' and
    last '}'. Crude but effective.
    """
    text = text.strip()

    # Strip markdown fences (```json or ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

    # Slice between outermost braces — handles preamble/postamble
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        return text[first : last + 1]

    return text  # Let json.loads fail informatively


def _clamp_score(value) -> int:
    """Coerce score to int and clamp to [1, 10]. Defensive against Claude
    occasionally returning floats or out-of-range values."""
    try:
        v = int(round(float(value)))
    except (TypeError, ValueError):
        v = 5
    return max(1, min(10, v))


def _format_transcript(transcript: list) -> str:
    """Turn the transcript list into a labeled, readable string for the prompt.

    Accepts both dicts and Pydantic models (the route may pass either).
    """
    lines = []
    for entry in transcript:
        role = entry.role if hasattr(entry, "role") else entry["role"]
        content = entry.content if hasattr(entry, "content") else entry["content"]
        label = "EXECUTIVE" if role == "assistant" else "PRESENTER"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)
