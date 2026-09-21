"""Server-side validation for lead fields (tasks 5.7, 5.9).

Pure functions with no database or LLM dependency, so they are easy to test.
Each validator returns a ValidationResult with a cleaned value on success
or a short, visitor-friendly error message on failure.
"""

import re
from dataclasses import dataclass

# Allow single-word names ("Hammad"). Set to 2 to require first + last name.
MIN_NAME_PARTS = 1

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")

PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "test.com", "domain.com", "yourdomain.com", "sample.com",
}
PLACEHOLDER_EMAIL_LOCALS = {
    "test", "tester", "abc", "abcd", "asdf", "qwerty", "xyz", "fake",
    "noemail", "none", "na", "null", "example", "name", "email", "user", "demo",
}
PLACEHOLDER_NAMES = {
    "test", "tester", "test user", "abc", "asdf", "qwerty", "xyz", "name",
    "full name", "na", "n/a", "none", "null", "john doe", "jane doe", "your name",
}

MAX_LENGTHS = {
    "full_name": 80,
    "email": 254,
    "contact_number": 20,
    "company_name": 120,
    "project_summary": 1000,
    "service_interest": 200,
    "timeline": 100,
    "budget_range": 100,
    "source_page": 300,
}


@dataclass
class ValidationResult:
    ok: bool
    value: str | None = None
    error: str | None = None


def _fail(message: str) -> ValidationResult:
    return ValidationResult(ok=False, error=message)


def validate_full_name(raw: str | None) -> ValidationResult:
    name = re.sub(r"\s+", " ", (raw or "").strip())
    if not name:
        return _fail("Please tell me your name.")
    if len(name) > MAX_LENGTHS["full_name"]:
        return _fail("That name looks too long. Could you share just your name?")
    if name.lower() in PLACEHOLDER_NAMES:
        return _fail("Please share your real name so the team knows who to contact.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'\-]*", name):
        return _fail("Please use letters only for your name.")
    if len(re.findall(r"[A-Za-z]", name)) < 2:
        return _fail("That name looks too short. Could you write it out?")
    if len(name.split(" ")) < MIN_NAME_PARTS:
        return _fail("Please share your full name (first and last).")
    return ValidationResult(ok=True, value=name)


def validate_email(raw: str | None) -> ValidationResult:
    email = (raw or "").strip().lower()
    if not email:
        return _fail("Please share your email address.")
    if len(email) > MAX_LENGTHS["email"] or ".." in email or not EMAIL_RE.match(email):
        return _fail("That email address doesn't look valid. Could you check it and send it again?")
    local, domain = email.rsplit("@", 1)
    if local.startswith(".") or local.endswith("."):
        return _fail("That email address doesn't look valid. Could you check it and send it again?")
    if domain in PLACEHOLDER_EMAIL_DOMAINS or local in PLACEHOLDER_EMAIL_LOCALS:
        return _fail("That looks like a placeholder email. Please share a real address the team can reach.")
    return ValidationResult(ok=True, value=email)


def validate_contact_number(raw: str | None) -> ValidationResult:
    text = (raw or "").strip()
    if not text:
        return _fail("Please share your phone number.")
    if not re.fullmatch(r"\+?[\d\s\-().]+", text):
        return _fail("Phone numbers can only contain digits, spaces, dashes and a leading +.")
    digits = re.sub(r"\D", "", text)
    if not 7 <= len(digits) <= 15:
        return _fail("That phone number doesn't look right. Please include the full number with area or country code.")
    if len(set(digits)) <= 2 or digits in "01234567890123456789" or digits in "98765432109876543210":
        return _fail("That looks like a placeholder number. Please share a real phone number.")
    cleaned = ("+" if text.startswith("+") else "") + digits
    return ValidationResult(ok=True, value=cleaned)


def validate_optional_text(field: str, raw: str | None) -> ValidationResult:
    """Optional fields (task 5.8): trimmed and length-limited, never blocking."""
    text = re.sub(r"\s+", " ", (raw or "").strip())
    if not text:
        return ValidationResult(ok=True, value=None)
    return ValidationResult(ok=True, value=text[: MAX_LENGTHS.get(field, 500)])


def validate_field(field: str, raw: str | None) -> ValidationResult:
    if field == "full_name":
        return validate_full_name(raw)
    if field == "email":
        return validate_email(raw)
    if field == "contact_number":
        return validate_contact_number(raw)
    return validate_optional_text(field, raw)