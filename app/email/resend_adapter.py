"""Email adapter using Resend (task 6.1, 6.6).

A small, dedicated abstraction so the rest of the app never talks to
Resend's API directly. Returns a structured DeliveryResult instead of
raising on provider failures, so the caller can persist delivery status
(task 6.4) and decide on retry behavior without try/except sprawl
everywhere.

Retries a few times on transient failures (network errors, 5xx) before
giving up, all within a single call - so exactly one EmailNotification
row is ever created per lead, with no risk of duplicate emails.
"""

import time
from dataclasses import dataclass

import resend

from app.core.config import get_settings

settings = get_settings()

# Short, bounded retry window - an email notification should not make
# the visitor wait long, but a couple of quick retries handles brief
# network blips or Resend rate-limit responses.
RETRY_DELAYS = [1, 3]  # seconds between attempt 1->2 and 2->3

# Errors worth retrying: transient/network issues and Resend's own
# server-side or rate-limit problems. NOT retried: bad API key, invalid
# recipient, malformed request - retrying those would just waste time
# and could not possibly succeed on a second try.
_TRANSIENT_MARKERS = ("timeout", "connection", "5", "rate limit", "too many requests")


def _is_transient(error_text: str) -> bool:
    lowered = error_text.lower()
    return any(marker in lowered for marker in _TRANSIENT_MARKERS)


@dataclass
class DeliveryResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None
    attempts: int = 1


def send_email(subject: str, html_body: str, to: str | None = None) -> DeliveryResult:
    """Send one email via Resend, retrying transient failures a few
    times. Never raises - failures come back as a DeliveryResult with
    success=False so the caller can save the error (task 6.5)."""
    if not settings.resend_api_key:
        return DeliveryResult(success=False, error_message="RESEND_API_KEY is not configured")

    resend.api_key = settings.resend_api_key
    recipient = to or settings.effective_lead_email_to

    last_error = "unknown error"
    for attempt in range(len(RETRY_DELAYS) + 1):
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
            return DeliveryResult(success=True, provider_message_id=message_id, attempts=attempt + 1)
        except Exception as exc:  # Resend's SDK raises various exception types
            last_error = str(exc)
            if attempt < len(RETRY_DELAYS) and _is_transient(last_error):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            break

    # Sanitized: str(exc) from Resend's SDK is a provider error message,
    # not a stack trace or request payload - safe to store (task 6.4).
    return DeliveryResult(success=False, error_message=last_error, attempts=attempt + 1)