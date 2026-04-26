"""
llm_client.py — Unified LLM Interface
=======================================
Agents call chat() and never touch provider-specific code.

Both providers receive the same inputs:
  - system: str         → the agent's persona/instruction prompt
  - messages: list      → [{"role": "user"|"assistant", "content": "..."}]
  - model: str          → model name from config.py
  - max_tokens: int

Both return the same thing: a plain string (the model's reply).

Groq uses OpenAI-compatible chat completions format.
Anthropic uses its own messages format (system is a separate param).
This file handles the difference so agents don't have to.
"""

from config import LLM_PROVIDER, GROQ_API_KEY, ANTHROPIC_API_KEY
from typing import List, Dict


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
) -> str:
    """
    Send a chat request to whichever provider is configured.

    Args:
        system:     The system prompt (agent persona / instructions).
        messages:   Conversation history as [{"role": ..., "content": ...}].
                    Roles must be "user" or "assistant" — works for both providers.
        model:      Model name string (from config.py).
        max_tokens: Maximum tokens in the response.

    Returns:
        The model's reply as a plain string.
    """
    if LLM_PROVIDER == "groq":
        return _chat_groq(system, messages, model, max_tokens)
    elif LLM_PROVIDER == "anthropic":
        return _chat_anthropic(system, messages, model, max_tokens)


def current_provider() -> str:
    """Useful for logging and the /health endpoint."""
    return LLM_PROVIDER


# ─── Provider Implementations ──────────────────────────────────────────────────

def _chat_groq(system: str, messages: List[Dict], model: str, max_tokens: int) -> str:
    """
    Groq uses OpenAI-compatible format.
    System prompt is injected as the first message with role="system".
    """
    full_messages = [{"role": "system", "content": system}] + messages

    response = _groq_client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _chat_anthropic(system: str, messages: List[Dict], model: str, max_tokens: int) -> str:
    """
    Anthropic takes system as a separate top-level parameter.
    Message roles must be "user" or "assistant" (same as Groq, so no remapping needed).
    """
    response = _anthropic_client.messages.create(
        model=model,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.content[0].text.strip()
