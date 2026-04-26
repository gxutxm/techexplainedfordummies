"""
agents/evaluator.py — Evaluator Agent
======================================
⚠️  THIS FILE IS OWNED BY PAIR B.
Pair A created the stub and the JSON schema. Pair B implements the logic.

The evaluator reads the full interview transcript and scores the presenter
on clarity, tone, and jargon usage.

Expected output JSON shape (must match schemas.py EvaluateResponse exactly):
{
  "clarity": 1-10,
  "tone": 1-10,
  "jargon_score": 1-10,
  "jargon_terms": [
    { "term": "<jargon word>", "suggestion": "<plain English alternative>" }
  ],
  "summary": "2-3 sentence overall summary of how the presenter did.",
  "top_fix": "Single most impactful improvement the presenter should make."
}
"""

import os
import json
import anthropic
from typing import List, Dict
from schemas import EvaluateResponse, JargonTerm

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"

EVALUATOR_SYSTEM_PROMPT = """You are an expert communication coach evaluating how well someone explained a technical topic to a non-technical executive audience.

You will receive:
1. The original source text (abstract or presentation) the interviewee was asked about
2. A full transcript of the interview

Your job is to evaluate ONLY the interviewee's responses (the "user" turns) on three dimensions:

CLARITY (1–10):
- 10 = Explanations are crisp, concrete, and immediately understandable
- 1 = Vague, confusing, or impossible to follow without domain knowledge

TONE (1–10):
- 10 = Confident, warm, engaging — perfect for an executive audience
- 1 = Defensive, robotic, overly academic, or dismissive

JARGON SCORE (1–10):
- 10 = Zero unnecessary jargon — every term is explained or avoided
- 1 = Heavy jargon used without explanation, audience would be lost

Also identify any specific jargon terms the interviewee used without explaining,
and suggest a plain-English alternative for each.

You MUST respond with ONLY valid JSON — no preamble, no markdown, no backticks.
The JSON must exactly match this shape:
{
  "clarity": <int 1-10>,
  "tone": <int 1-10>,
  "jargon_score": <int 1-10>,
  "jargon_terms": [
    { "term": "<term>", "suggestion": "<plain English>" }
  ],
  "summary": "<2-3 sentences summarizing overall communication effectiveness>",
  "top_fix": "<single most impactful improvement>"
}
"""


def evaluate_transcript(source_text: str, transcript: list) -> EvaluateResponse:
    """
    Evaluates the full interview transcript and returns structured feedback.
    Retries once if Claude returns malformed JSON.
    """
    transcript_text = _format_transcript(transcript)

    user_message = (
        f"SOURCE TEXT (what the presenter was asked about):\n"
        f"---\n{source_text}\n---\n\n"
        f"INTERVIEW TRANSCRIPT:\n"
        f"---\n{transcript_text}\n---\n\n"
        f"Please evaluate the presenter's communication and return ONLY the JSON object."
    )

    raw = _call_claude(user_message)
    return _parse_response(raw)


def _call_claude(user_message: str, retry: bool = True) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=EVALUATOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


def _parse_response(raw: str) -> EvaluateResponse:
    """
    Parse Claude's JSON response. Strips markdown fences if present.
    Retries with a stricter prompt if parsing fails.
    """
    # Strip potential markdown code fences
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(clean)
        jargon_terms = [
            JargonTerm(term=j["term"], suggestion=j["suggestion"])
            for j in data.get("jargon_terms", [])
        ]
        return EvaluateResponse(
            clarity=data["clarity"],
            tone=data["tone"],
            jargon_score=data["jargon_score"],
            jargon_terms=jargon_terms,
            summary=data["summary"],
            top_fix=data["top_fix"],
        )
    except (json.JSONDecodeError, KeyError) as e:
        # Return a safe fallback rather than crashing the whole request
        return EvaluateResponse(
            clarity=5,
            tone=5,
            jargon_score=5,
            jargon_terms=[],
            summary="Evaluation could not be parsed. Please try again.",
            top_fix="Re-run evaluation.",
        )


def _format_transcript(transcript: list) -> str:
    """Turn the transcript list into a readable string for the prompt."""
    lines = []
    for entry in transcript:
        role = entry.role if hasattr(entry, "role") else entry["role"]
        content = entry.content if hasattr(entry, "content") else entry["content"]
        label = "EXECUTIVE" if role == "assistant" else "PRESENTER"
        lines.append(f"{label}: {content}")
    return "\n\n".join(lines)
