import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.chat.orchestrator import handle_message
from app.db.models import ChatMessage, ChatSession
from app.db.session import get_db
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

    reply = handle_message(db, session.id, payload.message)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=reply.text,
        intent=reply.intent,
    )
    db.add(assistant_message)

    session.last_activity_at = datetime.now(timezone.utc)

    db.commit()

    return ChatMessageResponse(
        session_token=session.session_token,
        message=reply.text,
        intent=reply.intent,
    )
