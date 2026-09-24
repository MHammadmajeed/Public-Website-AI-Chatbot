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