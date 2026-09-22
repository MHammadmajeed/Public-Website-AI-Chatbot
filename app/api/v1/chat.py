import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.chat.orchestrator import handle_message
from app.db.models import ChatMessage, ChatSession, LeadSubmission
from app.db.session import get_db
from app.llm.base import LLMUnavailableError
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse

router = APIRouter()


def _get_or_create_session(db: Session, token: str | None, source_page: str | None) -> ChatSession:
    if token:
        session = db.query(ChatSession).filter(ChatSession.session_token == token).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Unknown session_token")
        return session

    session = ChatSession(
        session_token=secrets.token_urlsafe(24),
        source_page=source_page,
    )
    db.add(session)
    db.flush()
    return session


@router.post("/messages", response_model=ChatMessageResponse)
def post_chat_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    session = _get_or_create_session(db, payload.session_token, payload.source_page)

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    db.flush()

    was_already_completed = session.lead_state == "completed"

    try:
        reply = handle_message(
            db,
            session.id,
            payload.message,
            current_lead_state=session.lead_state,
            current_lead_data=session.lead_data,
            exclude_message_id=user_message.id,
        )
    except LLMUnavailableError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="The assistant is temporarily busy. Please try again in a moment.",
        )

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply.text,
        intent=reply.intent,
    )
    db.add(assistant_message)

    # Lead state is kept independently of the LLM (task 5.4) and survives
    # across turns because it is persisted on the session row here.
    session.lead_state = reply.lead_state
    session.lead_data = reply.lead_data
    session.last_activity_at = datetime.now(timezone.utc)

    # The lead just became complete THIS turn - persist it (tasks 5.7, 5.8).
    # was_already_completed guards against creating duplicate rows if the
    # visitor keeps chatting after completion.
    if reply.lead_state == "completed" and not was_already_completed:
        data = reply.lead_data
        db.add(
            LeadSubmission(
                session_id=session.id,
                full_name=data["full_name"],
                email=data["email"],
                contact_number=data["contact_number"],
                company_name=data.get("company_name"),
                project_summary=data.get("project_summary"),
                service_interest=data.get("service_interest"),
                timeline=data.get("timeline"),
                budget_range=data.get("budget_range"),
                source_page=data.get("source_page") or session.source_page,
            )
        )

    db.commit()

    return ChatMessageResponse(
        session_token=session.session_token,
        message=reply.text,
        intent=reply.intent,
    )