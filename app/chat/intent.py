"""Lightweight, deterministic intent detection (task 4.5).

This is intentionally a simple keyword/pattern matcher, not an ML
classifier - the knowledge base has a small, well-defined set of
categories, and a deterministic approach is easier to test, debug, and
explain than a black-box classifier for a project this size.

Its main practical job: broad "what do you do" style questions should
be routed to the `company` category before ranking, so they aren't
outranked by more narrowly-worded service records (the company_001
ranking issue found during Day 3 evaluation).
"""

import re
from dataclasses import dataclass

COMPANY_OVERVIEW_PATTERNS = [
    r"\bwhat do you do\b",
    r"\bwho are you\b",
    r"\babout (your|the) company\b",
    r"\btell me about (your|the) company\b",
    r"\bwhat is moinsystems\b",
    r"\bwhat does moinsystems.*do\b",
]

PRICING_PATTERNS = [
    r"\bhow much\b",
    r"\bcost\b",
    r"\bpricing\b",
    r"\bprice\b",
    r"\bquote\b",
    r"\bbudget\b",
]

CONTACT_PATTERNS = [
    r"\bcontact me\b",
    r"\bhire you\b",
    r"\bstart a project\b",
    r"\bget in touch\b",
    r"\breach out\b",
    r"\bwork with you\b",
    r"\bwant to start\b",
]

TECHNOLOGY_PATTERNS = [
    r"\bwhat technolog(y|ies)\b",
    r"\btech(nology)? stack\b",
    r"\bprogramming languages?\b",
    r"\b(which|what) (framework|language|database|cloud)s?\b",
    r"\bdo you use\b",
]

SERVICES_PATTERNS = [
    r"\bwhat services\b",
    r"\bservices\b",
    r"\bdo you (build|develop|make|create|offer|provide)\b",
    r"\bcan you (build|develop|make|create)\b",
    r"\bcustom software\b",
    r"\bweb (development|design)\b",
    r"\bmobile app",
]


@dataclass
class DetectedIntent:
    name: str
    category_filter: str | None


def detect_intent(query: str) -> DetectedIntent:
    q = query.lower()

    for pattern in COMPANY_OVERVIEW_PATTERNS:
        if re.search(pattern, q):
            return DetectedIntent(name="company_overview", category_filter="company")

    for pattern in PRICING_PATTERNS:
        if re.search(pattern, q):
            # Pricing content isn't in the ingested knowledge base yet
            # (see Day 2 notes) - no category filter, retrieval will
            # correctly return no strong match and the fallback applies.
            return DetectedIntent(name="pricing", category_filter=None)

    for pattern in CONTACT_PATTERNS:
        if re.search(pattern, q):
            return DetectedIntent(name="contact_request", category_filter=None)

    for pattern in TECHNOLOGY_PATTERNS:
        if re.search(pattern, q):
            return DetectedIntent(name="technology", category_filter=None)

    for pattern in SERVICES_PATTERNS:
        if re.search(pattern, q):
            return DetectedIntent(name="services", category_filter=None)

    return DetectedIntent(name="general", category_filter=None)