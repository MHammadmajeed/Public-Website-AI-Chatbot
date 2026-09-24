"""Notification email content for a completed lead (task 6.2)."""

import html
from datetime import datetime, timezone

from app.db.models import ChatMessage, ChatSession


def _row(label: str, value: str | None) -> str:
    if not value:
        return ""
    safe_value = html.escape(str(value))
    return f"<tr><td style='padding:4px 8px;font-weight:bold;'>{label}</td><td style='padding:4px 8px;'>{safe_value}</td></tr>"
def build_lead_notification(
    session: ChatSession,
    lead_data: dict,
    recent_messages: list[ChatMessage],
) -> tuple[str, str]:
    """Returns (subject, html_body) for a new-lead notification email."""
    full_name = lead_data.get("full_name", "Unknown")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # A short conversation summary: the last few user messages, so the
    # team has context without reading the full transcript.
    user_lines = [m.content for m in recent_messages if m.role == "user"][-5:]
    conversation_summary = (
        "<br>".join(f"&bull; {html.escape(line)}" for line in user_lines) or "(no prior messages)"
    )
    rows = "".join(
        [
            _row("Full name", full_name),
            _row("Email", lead_data.get("email")),
            _row("Contact number", lead_data.get("contact_number")),
            _row("Company", lead_data.get("company_name")),
            _row("Service interest", lead_data.get("service_interest")),
            _row("Project summary", lead_data.get("project_summary")),
            _row("Timeline", lead_data.get("timeline")),
            _row("Budget range", lead_data.get("budget_range")),
            _row("Source page", lead_data.get("source_page") or session.source_page),
            _row("Session token", session.session_token),
            _row("Timestamp", timestamp),
        ]
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
      <h2>New lead from the MoinSystems AI chatbot</h2>
      <table style="border-collapse: collapse;">{rows}</table>
      <h3>Recent conversation</h3>
      <p>{conversation_summary}</p>
    </div>
    """

    subject = f"New chatbot lead: {full_name}"
    return subject, html_body