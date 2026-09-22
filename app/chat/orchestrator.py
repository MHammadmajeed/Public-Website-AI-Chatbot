"""Chat orchestration service.

Given a chat session and a new user message, this:
1. detects intent (task 4.5 / 5.3) and uses it to filter retrieval,
2. retrieves grounded context (task 4.3),
3. builds a bounded recent-message window for continuity (task 4.4),
4. calls the configured LLM provider (task 4.1) when a real answer is needed,
5. falls back to an approved fixed message when retrieval finds
   nothing usable, instead of letting the model guess (task 4.8),
6. runs the deterministic lead-capture state machine (task 5.4-5.6),
   answering the visitor's question first before asking for lead
   details when practical (task 5.5).

This module has no FastAPI/HTTP concerns - the route (app/api/v1/chat.py)
is a thin wrapper around `handle_message`.
"""

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.chat.intent import detect_intent
from app.chat.prompts import FALLBACK_MESSAGE, build_system_prompt
from app.db.models import ChatMessage
from app.leads import state as lead_state
from app.llm.base import LLMMessage
from app.llm.factory import get_provider
from app.rag.retriever import build_context, retrieve

# How many prior messages (user + assistant combined) to include for
# continuity. Kept small deliberately - task 4.4 explicitly calls for
# "recent messages required for continuity", not unlimited history.
RECENT_MESSAGE_WINDOW = 6

_FOLLOWUP_MARKERS = re.compile(
    r"\b(that|it|those|this|more|else|also|too|same)\b", re.IGNORECASE
)


@dataclass
class ChatReply:
    text: str
    intent: str
    used_fallback: bool
    lead_state: str
    lead_data: dict


def _recent_history(db: Session, session_id, exclude_message_id=None) -> list[LLMMessage]:
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    if exclude_message_id is not None:
        # The current user message is already saved; it is added separately
        # at the end, so leave it out of the history to avoid sending it twice.
        query = query.filter(ChatMessage.id != exclude_message_id)
    query = query.order_by(ChatMessage.created_at.desc()).limit(RECENT_MESSAGE_WINDOW)
    rows = list(query)[::-1]  # oldest first
    return [LLMMessage(role=row.role, content=row.content) for row in rows]


def _followup_hint(user_text: str, history: list[LLMMessage]) -> str | None:
    """Only reuse the previous user message as retrieval context when the
    current question looks like a vague follow-up ("what about that?",
    "tell me more"), not for clear, self-contained new questions - this
    avoids an earlier topic (e.g. pricing) leaking into an unrelated one
    (e.g. technology)."""
    word_count = len(user_text.split())
    looks_like_followup = word_count <= 4 or bool(_FOLLOWUP_MARKERS.search(user_text))
    if not looks_like_followup:
        return None
    return next((m.content for m in reversed(history) if m.role == "user"), None)


def _answer_question(
    db: Session,
    session_id,
    user_text: str,
    detected,
    history: list[LLMMessage],
    current_lead_state: str,
    current_lead_data: dict,
) -> tuple[str, bool]:
    """Answer the visitor's actual question (task 4.3, 4.8). Returns (text, used_fallback)."""
    recent_hint = _followup_hint(user_text, history)

    result = retrieve(
        db,
        query=user_text,
        recent_context=recent_hint,
        category=detected.category_filter,
    )
    context = build_context(result)

    if not result.has_context:
        return FALLBACK_MESSAGE, True

    system_prompt = build_system_prompt(
        context,
        intent=detected.name,
        lead_state=current_lead_state,
    )

    provider = get_provider()
    reply_text = provider.generate(
        system_prompt=system_prompt,
        messages=history + [LLMMessage(role="user", content=user_text)],
    )
    return reply_text, False


def handle_message(
    db: Session,
    session_id,
    user_text: str,
    current_lead_state: str = lead_state.NOT_STARTED,
    current_lead_data: dict | None = None,
    exclude_message_id=None,
) -> ChatReply:
    current_lead_data = dict(current_lead_data or {})
    detected = detect_intent(user_text)
    history = _recent_history(db, session_id, exclude_message_id)

    # Let the lead state machine react first: it may consume this turn
    # entirely (collecting a field, handling yes/no to an offer), or it
    # may leave the state untouched because this is an ordinary question.
    decision = lead_state.decide(current_lead_state, current_lead_data, user_text, detected.name)

    if decision.state == lead_state.COLLECTING and decision.reply and not decision.append:
        # Actively mid-collection (asked for a field, got one, or an
        # invalid value) - the state machine's reply IS the answer this
        # turn. No LLM call needed.
        return ChatReply(
            text=decision.reply,
            intent=detected.name,
            used_fallback=False,
            lead_state=decision.state,
            lead_data=decision.data,
        )

    if decision.complete or (
        decision.state == lead_state.COMPLETED and decision.reply and decision.data == current_lead_data
    ):
        # Either the lead just finished this turn (complete=True), or it
        # was already complete and the visitor triggered a lead intent
        # again. Either way, the state machine's reply is the full answer.
        return ChatReply(
            text=decision.reply,
            intent=detected.name,
            used_fallback=False,
            lead_state=decision.state,
            lead_data=decision.data,
        )

    # Otherwise: answer the visitor's actual question first (task 5.5).
    answer_text, used_fallback = _answer_question(
        db, session_id, user_text, detected, history, decision.state, decision.data
    )

    final_text = answer_text
    if decision.append:
        # A question came in mid-collection: answer it, then remind them
        # what's still needed, preserving lead state (checklist item 27).
        final_text = f"{answer_text}\n\n{decision.append}"
    elif decision.reply and decision.state != current_lead_state:
        # A fresh pricing/contact intent just triggered the lead flow for
        # the first time this turn: answer, then offer/ask for details.
        final_text = f"{answer_text} {decision.reply}"

    return ChatReply(
        text=final_text,
        intent=detected.name,
        used_fallback=used_fallback,
        lead_state=decision.state,
        lead_data=decision.data,
    )