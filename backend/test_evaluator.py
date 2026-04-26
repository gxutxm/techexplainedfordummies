"""
test_evaluator.py — Standalone test harness for the evaluator agent
====================================================================
Run from the backend/ directory:
    cd backend
    python test_evaluator.py

Tests three things:
  1. End-to-end: real Claude/Groq call returns valid EvaluateResponse.
  2. JSON extraction: handles markdown fences, preamble, postamble.
  3. Score clamping: out-of-range values get coerced to [1, 10].

This does NOT touch the FastAPI server. It calls the agent directly so
you can iterate on the prompt without restarting uvicorn.
"""

import logging
import sys
import os

# Make sure we can import from backend/ regardless of where this is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.evaluator import (
    evaluate_transcript,
    _extract_json,
    _clamp_score,
    _try_parse,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')


# ─── Fixtures ─────────────────────────────────────────────────────────────────

FAKE_SOURCE = (
    "Our system uses a transformer-based architecture with multi-head attention "
    "to process sequential biomedical EEG signals for sleep stage classification. "
    "We achieved an F1 score of 0.87 on the Sleep-EDF benchmark, outperforming "
    "the baseline LSTM approach by 12 percentage points."
)

# A transcript that should score MEDIUM — some jargon, some clarity wins.
FAKE_TRANSCRIPT_MEDIUM = [
    {"role": "assistant", "content": "So what does your system actually do, in plain terms?"},
    {"role": "user", "content": "We use a transformer architecture with multi-head attention to perform sequence-to-sequence modeling on EEG data for sleep stage classification."},
    {"role": "assistant", "content": "I'm sorry — what's a transformer? Like the movie?"},
    {"role": "user", "content": "Ha, no — it's a type of neural network that's good at understanding sequences. Think of it like a really attentive reader who can remember what was said far back in a story."},
    {"role": "assistant", "content": "Okay, that helps. And what problem does this solve for our customers?"},
    {"role": "user", "content": "It improves the F1 score by 12 percentage points over the baseline LSTM approaches we previously used."},
    {"role": "assistant", "content": "I think we have what we need — thank you."},
]

# A transcript that should score HIGH — clear analogies, no unexplained jargon.
FAKE_TRANSCRIPT_GOOD = [
    {"role": "assistant", "content": "What does your system do?"},
    {"role": "user", "content": "It reads brain wave recordings while someone sleeps and figures out what stage of sleep they're in — light, deep, dreaming. It's about 12% more accurate than the previous best system."},
    {"role": "assistant", "content": "Why does that matter?"},
    {"role": "user", "content": "Doctors use sleep stage data to diagnose conditions like insomnia and sleep apnea. Today, a human technician has to label every 30-second window manually — it takes hours per patient. Our system does it in seconds with hospital-grade accuracy."},
    {"role": "assistant", "content": "Got it — thank you."},
]


# ─── Unit tests ───────────────────────────────────────────────────────────────

def test_extract_json_handles_fences():
    raw = '```json\n{"clarity": 7, "tone": 8}\n```'
    assert _extract_json(raw) == '{"clarity": 7, "tone": 8}', "Failed to strip ```json fences"
    print("  ✓ strips ```json code fences")

def test_extract_json_handles_preamble():
    raw = 'Here is your evaluation:\n{"clarity": 7, "tone": 8}'
    assert _extract_json(raw) == '{"clarity": 7, "tone": 8}', "Failed to strip preamble"
    print("  ✓ strips preamble before JSON")

def test_extract_json_handles_postamble():
    raw = '{"clarity": 7, "tone": 8}\n\nHope this helps!'
    assert _extract_json(raw) == '{"clarity": 7, "tone": 8}', "Failed to strip postamble"
    print("  ✓ strips postamble after JSON")

def test_clamp_score_in_range():
    assert _clamp_score(7) == 7
    assert _clamp_score(7.6) == 8       # rounds
    assert _clamp_score(15) == 10       # caps high
    assert _clamp_score(0) == 1         # caps low
    assert _clamp_score(-3) == 1        # caps negative
    assert _clamp_score("bad") == 5     # safe default
    assert _clamp_score(None) == 5
    print("  ✓ clamps scores to [1, 10] and handles bad input")

def test_try_parse_rejects_garbage():
    assert _try_parse("not json at all") is None
    assert _try_parse("") is None
    assert _try_parse('{"clarity": 7}') is None  # missing required fields
    print("  ✓ _try_parse returns None on unparseable / incomplete input")

def test_try_parse_accepts_valid():
    valid = (
        '{"clarity": 7, "tone": 8, "jargon_score": 6, '
        '"jargon_terms": [{"term": "RAG", "suggestion": "lookup-based AI"}], '
        '"summary": "Solid effort.", "top_fix": "Define jargon first."}'
    )
    result = _try_parse(valid)
    assert result is not None, "Failed to parse a known-good JSON blob"
    assert result.clarity == 7
    assert result.jargon_score == 6
    assert len(result.jargon_terms) == 1
    print("  ✓ _try_parse accepts well-formed JSON")


# ─── Integration test (real LLM call) ─────────────────────────────────────────

def test_end_to_end(transcript, label):
    print(f"\n[Integration: {label}]")
    print("  → Calling evaluator (this will hit the real LLM)...")
    try:
        result = evaluate_transcript(FAKE_SOURCE, transcript)
        print(f"  ✓ Got valid response")
        print(f"      clarity={result.clarity}  tone={result.tone}  jargon={result.jargon_score}")
        print(f"      jargon_terms: {len(result.jargon_terms)}")
        print(f"      summary: {result.summary[:80]}{'...' if len(result.summary) > 80 else ''}")
        print(f"      top_fix: {result.top_fix[:80]}{'...' if len(result.top_fix) > 80 else ''}")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False
    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 60)
    print("  Evaluator unit tests")
    print("═" * 60)
    test_extract_json_handles_fences()
    test_extract_json_handles_preamble()
    test_extract_json_handles_postamble()
    test_clamp_score_in_range()
    test_try_parse_rejects_garbage()
    test_try_parse_accepts_valid()

    print("\n" + "═" * 60)
    print("  Integration tests (real LLM)")
    print("═" * 60)

    if "--no-llm" in sys.argv:
        print("\n  Skipping LLM tests (--no-llm flag set)")
        sys.exit(0)

    ok1 = test_end_to_end(FAKE_TRANSCRIPT_MEDIUM, "medium-quality transcript")
    ok2 = test_end_to_end(FAKE_TRANSCRIPT_GOOD, "high-quality transcript")

    print("\n" + "═" * 60)
    if ok1 and ok2:
        print("  All integration tests passed.")
        sys.exit(0)
    else:
        print("  One or more integration tests FAILED.")
        sys.exit(1)
