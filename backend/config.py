"""
config.py — LLM Provider Configuration
========================================
Switch between Groq (dev/testing) and Anthropic (demo/prod) here.

To change provider: set LLM_PROVIDER in your .env file.
  LLM_PROVIDER=groq        → uses Groq API (fast, cheap, for building)
  LLM_PROVIDER=anthropic   → uses Anthropic Claude (for final demo)

Never hardcode provider logic in agents. Always import from here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Provider Selection ────────────────────────────────────────────────────────

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower()  # default to groq while building

assert LLM_PROVIDER in ("groq", "anthropic"), (
    f"Invalid LLM_PROVIDER='{LLM_PROVIDER}'. Must be 'groq' or 'anthropic'."
)

# ─── Model Names per Provider ─────────────────────────────────────────────────

MODELS = {
    "groq": {
        "interviewer": "llama-3.3-70b-versatile",   # Fast, smart, great for conversation
        "evaluator":   "llama-3.3-70b-versatile",
    },
    "anthropic": {
        "interviewer": "claude-sonnet-4-20250514",   # Switch to this for demo
        "evaluator":   "claude-sonnet-4-20250514",
    },
}

INTERVIEWER_MODEL = MODELS[LLM_PROVIDER]["interviewer"]
EVALUATOR_MODEL   = MODELS[LLM_PROVIDER]["evaluator"]

# ─── API Keys ─────────────────────────────────────────────────────────────────

GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Validate that the right key exists for the chosen provider
if LLM_PROVIDER == "groq" and not GROQ_API_KEY:
    raise EnvironmentError("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")

if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
    raise EnvironmentError("LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set in .env")

# ─── Token Limits ─────────────────────────────────────────────────────────────

MAX_TOKENS = {
    "interviewer": 300,
    "evaluator":   1000,
}
