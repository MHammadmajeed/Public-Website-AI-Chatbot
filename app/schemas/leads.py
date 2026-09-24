"""Request/response models for lead capture (task 5.10)."""

from pydantic import BaseModel, Field


from pydantic import BaseModel, Field


class LeadCaptureRequest(BaseModel):
    session_token: str = Field(..., max_length=64, description="Token from an existing chat session.")
    full_name: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=254)
    contact_number: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, max_length=120)
    project_summary: str | None = Field(default=None, max_length=1000)
    service_interest: str | None = Field(default=None, max_length=200)
    timeline: str | None = Field(default=None, max_length=100)
    budget_range: str | None = Field(default=None, max_length=100)
    source_page: str | None = Field(default=None, max_length=300)


class LeadCaptureResponse(BaseModel):
    lead_state: str
    missing_fields: list[str]
    message: str
    lead_id: str | None = None  # set once all required fields are collected and saved