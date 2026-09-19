"""Chat orchestration service.

Given a chat session and a new user message, this:
1. detects intent (task 4.5) and uses it to filter retrieval,
2. retrieves grounded context (task 4.3),
3. builds a bounded recent-message window for continuity (task 4.4),
4. calls the configured LLM provider (task 4.1),
5. falls back to an approved fixed message when retrieval finds
   nothing usable, instead of letting the model guess (task 4.8).

This module has no FastAPI/HTTP concerns - the route (app/api/v1/chat.py)
is a thin wrapper around `handle_message`.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.chat.intent import detect_intent
from app.chat.prompts import FALLBACK_MESSAGE, build_system_prompt
from app.db.models import ChatMessage
from app.llm.base import LLMMessage
from app.llm.factory import get_provider
from app.rag.retriever import build_context, retrieve

# How many prior messages (user + assistant combined) to include for
# continuity. Kept small deliberately - task 4.4 explicitly calls for
# "recent messages required for continuity", not unlimited history.
RECENT_MESSAGE_WINDOW = 6


@dataclass
class ChatReply:
    text: str
    intent: str
    used_fallback: bool


def _recent_history(db: Session, session_id, exclude_message_id=None) -> list[LLMMessage]:
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    if exclude_message_id is not None:
        # The current user message is already saved; it is added separately
        # at the end, so leave it out of the history to avoid sending it twice.
        query = query.filter(ChatMessage.id != exclude_message_id)
    query = query.order_by(ChatMessage.created_at.desc()).limit(RECENT_MESSAGE_WINDOW)
    rows = list(query)[::-1]  # oldest first
    return [LLMMessage(role=row.role, content=row.content) for row in rows]


def handle_message(db: Session, session_id, user_text: str, exclude_message_id=None) -> ChatReply:
    detected = detect_intent(user_text)

    history = _recent_history(db, session_id, exclude_message_id)

    # A short hint (the visitor's previous question, not the full history)
    # helps the retriever resolve follow-ups like "tell me more about the first one".
    recent_hint = next((m.content for m in reversed(history) if m.role == "user"), None)

    result = retrieve(
        db,
        query=user_text,
        recent_context=recent_hint,
        category=detected.category_filter,
    )
    context = build_context(result)

    if not result.has_context:
        # Approved fallback - deterministic, never sent to the LLM to
        # "guess" from. This guarantees no hallucination on unknowns
        # (task 4.8 / exit criteria).
        return ChatReply(text=FALLBACK_MESSAGE, intent=detected.name, used_fallback=True)

    system_prompt = build_system_prompt(
        context,
        intent=detected.name,
        lead_state="not_started",
    )

    provider = get_provider()
    reply_text = provider.generate(
        system_prompt=system_prompt,
        messages=history + [LLMMessage(role="user", content=user_text)],
    )

    return ChatReply(text=reply_text, intent=detected.name, used_fallback=False)