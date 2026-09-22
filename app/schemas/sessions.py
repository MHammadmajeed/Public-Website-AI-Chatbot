"""Request/response models for explicit session creation (task 5.10)."""

from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    source_page: str | None = None


class SessionCreateResponse(BaseModel):
    session_token: str