"""Notify the team about a completed lead, with delivery tracking
(tasks 6.2-6.6).
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ChatMessage, ChatSession, EmailNotification, LeadSubmission
from app.email.resend_adapter import send_email
from app.email.templates import build_lead_notification
from app.logging_config import app_logger

settings = get_settings()


def notify_lead(db: Session, session: ChatSession, lead: LeadSubmission) -> EmailNotification:
    """Send the lead notification email and persist delivery status
    (task 6.4). Never raises - the caller checks the returned status
    instead, so a chat reply can never claim success on a failed send
    (task 6.5)."""
    recent_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )[::-1]

    lead_data = {
        "full_name": lead.full_name,
        "email": lead.email,
        "contact_number": lead.contact_number,
        "company_name": lead.company_name,
        "project_summary": lead.project_summary,
        "service_interest": lead.service_interest,
        "timeline": lead.timeline,
        "budget_range": lead.budget_range,
        "source_page": lead.source_page,
    }

    subject, html_body = build_lead_notification(session, lead_data, recent_messages)
    result = send_email(subject, html_body)

    notification = EmailNotification(
        lead_id=lead.id,
        recipient=settings.effective_lead_email_to,
        subject=subject,
        status="sent" if result.success else "failed",
        provider_message_id=result.provider_message_id,
        sent_at=datetime.now(timezone.utc) if result.success else None,
        error_message=result.error_message,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    app_logger.info(
        "lead_notification_sent" if result.success else "lead_notification_failed",
        extra={
            "lead_id": str(lead.id),
            "status": notification.status,
            "attempts": result.attempts,
            # error_message from Resend's SDK is a short provider message,
            # not a stack trace - safe to log (task 6.11).
            "error": result.error_message,
        },
    )
    return notification