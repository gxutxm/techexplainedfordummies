"""
agents/interviewer.py — Interviewer Agent (Executive Persona)
=============================================================
This agent plays a non-technical executive conducting a follow-up interview
about a technical abstract or presentation.

Behavior:
- Asks ONE focused follow-up question at a time
- Stays in character as a curious, non-technical executive
- Avoids jargon, asks for plain-language explanations
- After MAX_TURNS, wraps up the interview gracefully
"""

from typing import List, Dict
import llm_client
from config import INTERVIEWER_MODEL, MAX_TOKENS

MAX_TURNS = 6  # Number of user responses before the interview ends

SYSTEM_PROMPT = """You are a senior non-technical executive (C-suite level) conducting a follow-up interview with someone who just presented a technical project or research paper to you.

Your character:
- Curious, engaged, and genuinely interested — but not technical
- You speak plainly and expect plain answers
- You ask ONE short, focused follow-up question at a time
- You never use technical jargon yourself
- You represent the business perspective: impact, clarity, feasibility, ROI

Your job in this interview:
- Probe for clarity on what the project actually does in plain terms
- Ask about real-world impact or use cases
- Ask who the audience or users are
- Ask what problem it solves and why it matters now
- Ask what success looks like
- Challenge vague or overly technical answers by asking for simpler explanations

Rules you MUST follow:
- Ask ONLY ONE question per response — never multiple questions at once
- Keep your responses SHORT (2–4 sentences max): a brief reaction + one question
- Never summarize or repeat back what was said at length
- Stay in character — you are the executive, not an AI assistant
- Do NOT use bullet points, numbered lists, or headers
- Sound natural and conversational, like a real person speaking

When ending the interview (you will be told when this is the final turn):
- Thank the presenter warmly
- Give a one-sentence impression
- End with something like "I think we have what we need — thank you for your time."
- Do NOT ask another question
"""


def build_messages(source_text: str, transcript: List[Dict]) -> List[Dict]:
    """
    Build the messages array for the Claude API call.
    
    The source text is injected into the first user message so the agent
    has full context about what was presented.
    """
    messages = []

    # First message: give the agent the abstract to read
    messages.append({
        "role": "user",
        "content": (
            f"Here is the abstract/presentation I want you to interview me about:\n\n"
            f"---\n{source_text}\n---\n\n"
            f"Please begin the interview with your first question."
        )
    })

    # Replay the existing transcript
    for entry in transcript:
        messages.append({
            "role": entry["role"] if isinstance(entry, dict) else entry.role,
            "content": entry["content"] if isinstance(entry, dict) else entry.content,
        })

    return messages


def get_first_question(source_text: str) -> str:
    """
    Called when a session starts. Returns the agent's opening question.
    """
    messages = [
        {
            "role": "user",
            "content": (
                f"Here is the abstract/presentation I want you to interview me about:\n\n"
                f"---\n{source_text}\n---\n\n"
                f"Please begin the interview with your first question. "
                f"React briefly (1 sentence) to what you just read, then ask your first question."
            )
        }
    ]

    return llm_client.chat(
        system=SYSTEM_PROMPT,
        messages=messages,
        model=INTERVIEWER_MODEL,
        max_tokens=MAX_TOKENS["interviewer"],
    )


def get_next_question(source_text: str, transcript: list, turn_count: int) -> str:
    """
    Called after each user reply. Returns the agent's next question.
    If turn_count >= MAX_TURNS, the agent wraps up instead of asking more.
    """
    is_final_turn = turn_count >= MAX_TURNS

    messages = build_messages(source_text, transcript)

    # Inject instruction about ending if this is the last turn
    if is_final_turn:
        messages.append({
            "role": "user",
            "content": (
                "[SYSTEM NOTE — NOT VISIBLE TO PRESENTER]: "
                "This is the final turn. Do NOT ask another question. "
                "Wrap up the interview warmly with a brief closing remark and thank the presenter."
            )
        })

    return llm_client.chat(
        system=SYSTEM_PROMPT,
        messages=messages,
        model=INTERVIEWER_MODEL,
        max_tokens=MAX_TOKENS["interviewer"],
    )


def is_interview_complete(turn_count: int) -> bool:
    return turn_count >= MAX_TURNS
