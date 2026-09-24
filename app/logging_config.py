"""Structured logging setup (task 6.11).

Logs as one-line JSON so they're easy to search/filter on Render or any
log aggregator. Deliberately logs identifiers and outcomes, never full
message content, lead field values, or secrets.
"""

import logging
import sys

from pythonjsonlogger import json as jsonlogger


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # Quiet down noisy third-party loggers so our own events aren't buried.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


app_logger = logging.getLogger("moin_chatbot")