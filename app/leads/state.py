"""Deterministic lead-capture state machine (tasks 5.4 to 5.8).

The backend, not the LLM, decides which lead detail is still missing.
Everything here is plain Python: no database and no LLM calls, so it is
easy to test.

States:
    not_started : lead capture has not begun
    offered     : the bot asked "would you like to share your details?"
    collecting  : the visitor agreed; required fields are asked one at a time
    completed   : all required fields collected
    declined    : the visitor said no; do not ask again unless they show high intent
"""

import re
from dataclasses import dataclass, field

from app.leads.validation import (
    validate_contact_number,
    validate_email,
    validate_full_name,
    validate_optional_text,
)

NOT_STARTED = "not_started"
OFFERED = "offered"
COLLECTING = "collecting"
COMPLETED = "completed"
DECLINED = "declined"

REQUIRED_FIELDS = ["full_name", "email", "contact_number"]

FIELD_PROMPTS = {
    "full_name": "May I have your full name?",
    "email": "What's the best email address to reach you?",
    "contact_number": "And what phone number can the team reach you on?",
}

PRICING_EXPLANATION = (
    "Pricing depends on the scope of your project, such as the features, integrations and "
    "timeline, so our team prepares a tailored quote after understanding your requirements."
)
PRICING_INTRO = PRICING_EXPLANATION + " I can pass your details to our team so they can follow up."
CONTACT_INTRO = "Great, we'd be glad to help with that! I can pass your details to our team."
REMINDER = "To continue with your request:"
DECLINE_REPLY = (
    "No problem at all. Feel free to ask me anything else about MoinSystems AI, "
    "and you can share your details any time."
)
ALREADY_CAPTURED_REPLY = "Our team already has your details and will follow up with you soon."

LEAD_INTENTS = {"pricing", "contact_request"}

EMAIL_FIND = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
PHONE_FIND = re.compile(r"\+?\d[\d\s\-().]{5,}\d")
NAME_PREFIX = re.compile(
    r"^\s*(?:my name is|my name's|i am|i'm|im|this is|it is|it's|call me|name is|name:)\s+",
    re.IGNORECASE,
)
AFFIRMATIVE = re.compile(
    r"^\s*(?:yes|yeah|yep|yup|sure|ok|okay|please|go ahead|of course|definitely|sounds good|y)\b",
    re.IGNORECASE,
)
NEGATIVE = re.compile(
    r"^\s*(?:no|nope|nah|not now|no thanks|no thank you|maybe later|skip|not interested|never mind|nevermind)\b",
    re.IGNORECASE,
)
QUESTION_STARTERS = {
    "what", "how", "do", "does", "did", "can", "could", "would", "are", "is", "who",
    "where", "when", "why", "which", "tell", "show", "explain", "give", "you", "your",
    "we", "hi", "hello", "hey", "thanks", "thank", "please", "yes", "no", "ok", "okay",
}

COMPANY_RE = re.compile(
    r"(?:my company is|company name is|i work (?:at|for)|we are from|i'm from|i am from)\s+"
    r"([A-Za-z0-9][A-Za-z0-9 &.\-]{1,60})",
    re.IGNORECASE,
)
COMPANY_CUT = re.compile(r"\s+(?:and|but|we|because|so|who|which)\b|[,.;]", re.IGNORECASE)
TIMELINE_RE = re.compile(
    r"\b(asap|urgent(?:ly)?|(?:within|in|by)\s+(?:the next\s+)?\d+\s*(?:day|week|month|year)s?"
    r"|next (?:week|month|quarter)|this (?:week|month|quarter))\b",
    re.IGNORECASE,
)
BUDGET_RE = re.compile(
    r"(?:\$|\b(?:usd|pkr|rs)\b\.?)\s?\d[\d,]*(?:\.\d+)?\s?[km]?\b"
    r"|\b\d[\d,]*\s?(?:usd|pkr|dollars|rupees|k)\b",
    re.IGNORECASE,
)


@dataclass
class Decision:
    state: str                        # lead state after this turn
    data: dict = field(default_factory=dict)  # collected fields after this turn
    reply: str | None = None          # deterministic reply (skip the LLM) when set
    append: str | None = None         # text to add after the LLM's answer
    complete: bool = False            # True when all required fields are now collected


@dataclass
class Extraction:
    updates: dict = field(default_factory=dict)
    error: str | None = None
    attempted: bool = False


def next_missing_field(data: dict) -> str | None:
    for name in REQUIRED_FIELDS:
        if not data.get(name):
            return name
    return None


def wants_lead_capture(intent: str) -> bool:
    return intent in LEAD_INTENTS


def is_affirmative(text: str) -> bool:
    return bool(AFFIRMATIVE.match(text or ""))


def is_negative(text: str) -> bool:
    return bool(NEGATIVE.match(text or ""))


def _looks_like_name(text: str) -> bool:
    words = text.split()
    if not 1 <= len(words) <= 4 or "?" in text:
        return False
    return words[0].lower().strip(".,!") not in QUESTION_STARTERS


def _record(ex: Extraction, field_name: str, result) -> None:
    if result.ok:
        ex.updates[field_name] = result.value
    elif ex.error is None:
        ex.error = result.error


def extract_fields(text: str, data: dict, awaiting: str | None) -> Extraction:
    """Pull required fields out of a visitor message (tasks 5.7, 5.9).

    `awaiting` is the required field we asked for last. `attempted` is False
    when the message looks like an ordinary question instead of an answer.
    """
    ex = Extraction()
    remaining = (text or "").strip()

    email_match = EMAIL_FIND.search(remaining)
    if email_match:
        ex.attempted = True
        _record(ex, "email", validate_email(email_match.group(0)))
        remaining = remaining.replace(email_match.group(0), " ")

    phone_match = PHONE_FIND.search(remaining)
    if phone_match:
        ex.attempted = True
        _record(ex, "contact_number", validate_contact_number(phone_match.group(0)))
        remaining = remaining.replace(phone_match.group(0), " ")

    if awaiting == "full_name" and "full_name" not in ex.updates:
        candidate = NAME_PREFIX.sub("", remaining)
        candidate = re.sub(r"\s+", " ", candidate).strip(" ,;:-.\n\t")
        if candidate and _looks_like_name(candidate):
            ex.attempted = True
            _record(ex, "full_name", validate_full_name(candidate))

    if not ex.attempted:
        clean = (text or "").strip()
        single_token = len(clean.split()) == 1 and "?" not in clean
        if awaiting == "email" and ("@" in clean or single_token):
            ex.attempted = True
            _record(ex, "email", validate_email(clean))
        elif awaiting == "contact_number" and (
            single_token or sum(ch.isdigit() for ch in clean) >= 5
        ):
            ex.attempted = True
            _record(ex, "contact_number", validate_contact_number(clean))

    return ex


def extract_optional_fields(text: str) -> dict:
    """Optional fields (task 5.8), captured only when they appear naturally."""
    found: dict = {}
    text = text or ""

    company = COMPANY_RE.search(text)
    if company:
        name = COMPANY_CUT.split(company.group(1))[0].strip()
        if name:
            found["company_name"] = name

    timeline = TIMELINE_RE.search(text)
    if timeline:
        found["timeline"] = timeline.group(1).strip()

    budget = BUDGET_RE.search(text)
    if budget:
        found["budget_range"] = budget.group(0).strip()

    return found


def _completed_reply(data: dict) -> str:
    first_name = (data.get("full_name") or "there").split(" ")[0]
    return (
        f"Thank you, {first_name}! I've passed your details to our team, and they'll "
        "follow up with you soon. Is there anything else I can help you with?"
    )


def _start_collecting(data: dict, text: str, intent: str) -> Decision:
    # Pick up any required details already in the message, but ignore errors here.
    ex = extract_fields(text, data, None)
    data.update(ex.updates)
    for key, value in extract_optional_fields(text).items():
        data.setdefault(key, value)
    if len(text) >= 15 and "project_summary" not in data:
        summary = validate_optional_text("project_summary", text).value
        if summary:
            data["project_summary"] = summary

    missing = next_missing_field(data)
    if missing is None:
        return Decision(COMPLETED, data, reply=_completed_reply(data), complete=True)

    intro = PRICING_INTRO if intent == "pricing" else CONTACT_INTRO
    return Decision(COLLECTING, data, reply=f"{intro} {FIELD_PROMPTS[missing]}")


def _handle_collecting(data: dict, text: str, intent: str) -> Decision:
    if is_negative(text):
        return Decision(DECLINED, data, reply=DECLINE_REPLY)

    awaiting = next_missing_field(data)
    if awaiting is None:
        return Decision(COMPLETED, data, reply=_completed_reply(data), complete=True)

    ex = extract_fields(text, data, awaiting)

    if not ex.attempted:
        # The visitor asked something else. State is preserved (checklist item 27).
        if intent == "pricing":
            return Decision(
                COLLECTING, data, reply=f"{PRICING_EXPLANATION} {FIELD_PROMPTS[awaiting]}"
            )
        return Decision(COLLECTING, data, append=f"{REMINDER} {FIELD_PROMPTS[awaiting]}")

    data.update(ex.updates)
    for key, value in extract_optional_fields(text).items():
        data.setdefault(key, value)

    if ex.error:
        return Decision(COLLECTING, data, reply=ex.error)

    missing = next_missing_field(data)
    if missing is None:
        return Decision(COMPLETED, data, reply=_completed_reply(data), complete=True)
    return Decision(COLLECTING, data, reply=f"Thanks! {FIELD_PROMPTS[missing]}")


def decide(
    state: str,
    data: dict,
    text: str,
    intent: str,
    offered_by_bot: bool = False,
) -> Decision:
    """Decide what happens to the lead flow for one visitor message."""
    data = dict(data or {})
    text = (text or "").strip()

    if state == COLLECTING:
        return _handle_collecting(data, text, intent)

    if state == OFFERED or offered_by_bot:
        if is_affirmative(text):
            missing = next_missing_field(data) or "full_name"
            return Decision(COLLECTING, data, reply=f"Great! {FIELD_PROMPTS[missing]}")
        if is_negative(text):
            return Decision(DECLINED, data, reply=DECLINE_REPLY)

    if wants_lead_capture(intent):
        if state == COMPLETED:
            reply = ALREADY_CAPTURED_REPLY
            if intent == "pricing":
                reply = f"{PRICING_EXPLANATION} {ALREADY_CAPTURED_REPLY}"
            return Decision(COMPLETED, data, reply=reply)
        return _start_collecting(data, text, intent)

    return Decision(state, data)