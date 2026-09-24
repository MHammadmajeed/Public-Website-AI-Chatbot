# Decision: Streaming (Task 4.10)

Decision: Streaming is NOT used in v1. The chat endpoint returns one complete JSON response.

Reasons:
- Answers are short (max ~600 tokens), so waiting for the full reply is fast.
- Error handling stays correct: provider failures (503/429) are turned into a clean HTTP error before any response is sent. With streaming, an error mid-stream would leave the widget with a half-finished answer.
- The free-tier LLM has strict rate limits, so simple request/response is easier to retry and test.
- The React widget stays simpler, with no stream parsing needed.

Revisit if: average response time becomes noticeable to visitors, or answers get much longer.

# Decision: CORS Origins (Task 6.8)

Decision: ALLOWED_ORIGINS is restricted to explicit, comma-separated origins only
(no wildcards). Currently set to http://localhost:3000 for local development.

When deployed to Render, this will be updated to the real production frontend
domain(s), e.g. https://moinsystemsai.com. Wildcard origins (*) are never used,
since the chatbot API also handles lead data.

# Verification: Secret Management (Task 6.9)

Confirmed 2026-09-24:
- No hardcoded API keys, database URLs, or passwords found in app/ source code.
- .env is listed in .gitignore and has never been committed to git history
  (verified with `git log --all --full-history -- .env`).
- All secrets (DATABASE_URL, GEMINI_API_KEY, RESEND_API_KEY, APP_SECRET) load
  from environment variables via app/core/config.py, with no fallback to
  hardcoded values for sensitive fields.
- On deployment, these will be set as Render environment variables/secrets
  rather than committed anywhere.