from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_token: str | None = Field(
        default=None,
        description="Omit on the first message of a conversation; the server creates a new "
        "session and returns its token for you to reuse on subsequent messages.",
    )
    source_page: str | None = Field(
        default=None, description="URL of the page the widget is embedded on, for analytics."
    )


class ChatMessageResponse(BaseModel):
    session_token: str
    message: str
    intent: str
    # Deliberately excludes retrieval metadata (record IDs, similarity
    # scores, system prompt) per Day 4 exit criteria: internal prompts
    # and retrieval metadata must not be exposed to the client.
