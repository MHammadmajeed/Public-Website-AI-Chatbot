"""POST /api/v1/lead-capture (task 5.10).

Lets the widget submit lead fields directly (e.g. from a form fallback,
or fields the visitor typed that the chat flow already parsed), running
them through the same deterministic state machine and validation used
in chat (tasks 5.4, 5.7, 5.8, 5.9). Saves to lead_submission once all
required fields are present.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import ChatSession, LeadSubmission
from app.db.session import get_db
from app.leads import state as lead_state
from app.leads.validation import validate_field
from app.schemas.leads import LeadCaptureRequest, LeadCaptureResponse

router = APIRouter()

OPTIONAL_FIELDS = [
    "company_name",
    "project_summary",
    "service_interest",
    "timeline",
    "budget_range",
    "source_page",
]


@router.post("", response_model=LeadCaptureResponse)
def capture_lead(payload: LeadCaptureRequest, db: Session = Depends(get_db)):
    session = (
        db.query(ChatSession).filter(ChatSession.session_token == payload.session_token).first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session_token")

    data = dict(session.lead_data or {})

    # Validate every field the caller supplied (task 5.9) before merging it in.
    for field_name in lead_state.REQUIRED_FIELDS + OPTIONAL_FIELDS:
        raw = getattr(payload, field_name, None)
        if raw is None:
            continue
        result = validate_field(field_name, raw)
        if not result.ok:
            return LeadCaptureResponse(
                lead_state=session.lead_state,
                missing_fields=[
                    f for f in lead_state.REQUIRED_FIELDS if not data.get(f)
                ],
                message=result.error,
            )
        if result.value is not None:
            data[field_name] = result.value

    missing = [f for f in lead_state.REQUIRED_FIELDS if not data.get(f)]

    if missing:
        session.lead_state = lead_state.COLLECTING
        session.lead_data = data
        db.commit()
        return LeadCaptureResponse(
            lead_state=session.lead_state,
            missing_fields=missing,
            message=f"Thanks! {lead_state.FIELD_PROMPTS[missing[0]]}",
        )

    # All required fields present - persist the lead (task 5.7, 5.8).
    lead = LeadSubmission(
        session_id=session.id,
        full_name=data["full_name"],
        email=data["email"],
        contact_number=data["contact_number"],
        company_name=data.get("company_name"),
        project_summary=data.get("project_summary"),
        service_interest=data.get("service_interest"),
        timeline=data.get("timeline"),
        budget_range=data.get("budget_range"),
        source_page=data.get("source_page"),
    )
    db.add(lead)

    session.lead_state = lead_state.COMPLETED
    session.lead_data = data
    db.commit()
    db.refresh(lead)

    return LeadCaptureResponse(
        lead_state=session.lead_state,
        missing_fields=[],
        message=lead_state._completed_reply(data),
        lead_id=str(lead.id),
    )