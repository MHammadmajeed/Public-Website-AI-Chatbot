"""POST /api/v1/sessions (task 5.10) - explicit session creation.

Most visitors get a session implicitly on their first chat message
(see app/api/v1/chat.py), but the widget may call this up front to get
a session_token before the visitor types anything.
"""

import secrets

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import ChatSession
from app.db.session import get_db
from app.schemas.sessions import SessionCreateRequest, SessionCreateResponse

router = APIRouter()


@router.post("", response_model=SessionCreateResponse)
def create_session(payload: SessionCreateRequest, db: Session = Depends(get_db)):
    session = ChatSession(
        session_token=secrets.token_urlsafe(24),
        source_page=payload.source_page,
    )
    db.add(session)
    db.commit()
    return SessionCreateResponse(session_token=session.session_token)