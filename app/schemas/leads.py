"""Request/response models for lead capture (task 5.10)."""

from pydantic import BaseModel, Field


class LeadCaptureRequest(BaseModel):
    session_token: str = Field(..., description="Token from an existing chat session.")
    full_name: str | None = None
    email: str | None = None
    contact_number: str | None = None
    company_name: str | None = None
    project_summary: str | None = None
    service_interest: str | None = None
    timeline: str | None = None
    budget_range: str | None = None
    source_page: str | None = None


class LeadCaptureResponse(BaseModel):
    lead_state: str
    missing_fields: list[str]
    message: str
    lead_id: str | None = None  # set once all required fields are collected and saved