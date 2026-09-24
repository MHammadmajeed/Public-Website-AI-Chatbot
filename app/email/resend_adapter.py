"""Email adapter using Resend (task 6.1).

A small, dedicated abstraction so the rest of the app never talks to
Resend's API directly. Returns a structured DeliveryResult instead of
raising on provider failures, so the caller can persist delivery status
(task 6.4) and decide on retry behavior (task 6.6) without try/except
sprawl everywhere.
"""

from dataclasses import dataclass

import resend

from app.core.config import get_settings

settings = get_settings()


@dataclass
class DeliveryResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None


def send_email(subject: str, html_body: str, to: str | None = None) -> DeliveryResult:
    """Send one email via Resend. Never raises - failures come back as a
    DeliveryResult with success=False so the caller can save the error
    and decide whether to retry (task 6.5, 6.6)."""
    if not settings.resend_api_key:
        return DeliveryResult(success=False, error_message="RESEND_API_KEY is not configured")

    resend.api_key = settings.resend_api_key
    recipient = to or settings.effective_lead_email_to

    try:
        response = resend.Emails.send(
            {
                "from": "MoinSystems AI Chatbot <onboarding@resend.dev>",
                "to": [recipient],
                "subject": subject,
                "html": html_body,
            }
        )
        message_id = response.get("id") if isinstance(response, dict) else None
        return DeliveryResult(success=True, provider_message_id=message_id)
    except Exception as exc:  # Resend's SDK raises various exception types
        # Sanitized: str(exc) from Resend's SDK is a provider error message,
        # not a stack trace or request payload - safe to store (task 6.4).
        return DeliveryResult(success=False, error_message=str(exc))