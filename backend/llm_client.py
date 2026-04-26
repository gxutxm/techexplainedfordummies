"""
llm_client.py — Unified LLM Interface
=======================================
Agents call chat() and never touch provider-specific code.

Both providers receive the same inputs:
  - system: str         → the agent's persona/instruction prompt
  - messages: list      → [{"role": "user"|"assistant", "content": "..."}]
  - model: str          → model name from config.py
  - max_tokens: int
  - temperature: float  → optional; 0.0 for deterministic, higher for creative

Both return the same thing: a plain string (the model's reply).

Groq uses OpenAI-compatible chat completions format.
Anthropic uses its own messages format (system is a separate param).
This file handles the difference so agents don't have to.
"""

from typing import List, Dict, Optional

from config import LLM_PROVIDER, GROQ_API_KEY, ANTHROPIC_API_KEY


# ─── Initialize the right client once at import time ──────────────────────────

if LLM_PROVIDER == "groq":
    from groq import Groq
    _groq_client = Groq(api_key=GROQ_API_KEY)

elif LLM_PROVIDER == "anthropic":
    import anthropic
    _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─── Public Interface ──────────────────────────────────────────────────────────

def chat(
    system: str,
    messages: List[Dict[str, str]],
    model: str,
    max_tokens: int = 500,
    temperature: Optional[float] = None,
) -> str:
    """
    Send a chat request to whichever provider is configured.

    Args:
        system:      The system prompt (agent persona / instructions).
        messages:    Conversation history as [{"role": ..., "content": ...}].
                     Roles must be "user" or "assistant" — works for both providers.
        model:       Model name string (from config.py).
        max_tokens:  Maximum tokens in the response.
        temperature: Sampling temperature.
                       - None  → use provider default (0.7-ish, conversational)
                       - 0.0   → deterministic (use this for evaluator / JSON output)
                       - 1.0+  → creative

    Returns:
        The model's reply as a plain string.
    """
    if LLM_PROVIDER == "groq":
        return _chat_groq(system, messages, model, max_tokens, temperature)
    elif LLM_PROVIDER == "anthropic":
        return _chat_anthropic(system, messages, model, max_tokens, temperature)


def current_provider() -> str:
    """Useful for logging and the /health endpoint."""
    return LLM_PROVIDER


# ─── Provider Implementations ──────────────────────────────────────────────────

def _chat_groq(
    system: str,
    messages: List[Dict],
    model: str,
    max_tokens: int,
    temperature: Optional[float],
) -> str:
    """
    Groq uses OpenAI-compatible format.
    System prompt is injected as the first message with role="system".
    """
    full_messages = [{"role": "system", "content": system}] + messages

    kwargs = {
        "model": model,
        "messages": full_messages,
        "max_tokens": max_tokens,
        "temperature": 0.7 if temperature is None else temperature,
    }

    response = _groq_client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def _chat_anthropic(
    system: str,
    messages: List[Dict],
    model: str,
    max_tokens: int,
    temperature: Optional[float],
) -> str:
    """
    Anthropic takes system as a separate top-level parameter.
    Message roles must be "user" or "assistant" (same as Groq, so no remapping needed).
    """
    kwargs = {
        "model": model,
        "system": system,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    # Only pass temperature if explicitly set — let Anthropic use its default otherwise
    if temperature is not None:
        kwargs["temperature"] = temperature

    response = _anthropic_client.messages.create(**kwargs)
    return response.content[0].text.strip()
