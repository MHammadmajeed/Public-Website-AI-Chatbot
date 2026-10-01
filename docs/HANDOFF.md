# Project Handoff — MoinSystems AI Chatbot

**Status as of Day 8 (final):** Core system complete and tested end-to-end locally. Backend not yet deployed to a public URL — see `docs/DEPLOYMENT.md` for the deploy procedure.

## What this is

An AI-powered chat widget for the MoinSystems AI website that:
- Answers visitor questions using RAG (retrieval-augmented generation) grounded in company content
- Detects visitor intent (company overview, pricing, contact, technology, services, general)
- Naturally offers to collect contact details when intent is `pricing` or `contact_request`
- Captures and validates lead info, saves it to the database, and emails the team

## Where everything lives

| Area | Location |
|---|---|
| Backend (FastAPI) | `app/` |
| Intent detection | `app/chat/intent.py` |
| Orchestration (answer + lead-flow logic) | `app/chat/orchestrator.py` |
| Lead state machine & validation | `app/leads/` |
| API routes | `app/api/v1/` |
| Pydantic schemas | `app/schemas/` |
| DB models / session | `app/db/` |
| RAG ingestion & evaluation scripts | `scripts/` |
| Frontend widget (React + TS) | `frontend/src/` |
| Deployment guide | `docs/DEPLOYMENT.md` |
| Latest RAG evaluation | `eval_report_day8.txt` |

## What's working (verified)

- End-to-end chat flow: widget → API → RAG retrieval → Gemini → response
- Session continuity across multiple messages
- Lead capture form (frontend) + backend validation + DB save, confirmed via direct DB query
- Rate limiting on both chat (20/min) and lead-capture (10/min) endpoints, per-IP
- CORS configured correctly for local dev
- Accessibility pass: aria-live regions, focus management, screen-reader labels, contrast fixes
- Responsive design: mobile full-screen, desktop floating widget
- `.env` confirmed never committed to git history

## Known limitations

See `docs/DEPLOYMENT.md`'s "Known limitations" section — summary: Gemini free tier can be slow/flaky (503s with retry), Resend free tier restricts send-to address, RAG retrieval sits at 84.4% Top-5 accuracy with near-miss failures on semantically similar FAQ content.

## Not yet done

- Backend not deployed to a public URL (Render Web Service — steps documented in `docs/DEPLOYMENT.md`)
- Frontend widget not yet hosted anywhere public
- `ALLOWED_ORIGINS` needs the production frontend URL added once that's hosted
- No automated CI/CD — deploys are manual via Render's GitHub integration

## For whoever picks this up next

1. Read `docs/DEPLOYMENT.md` first — it has the full environment variable list and deploy steps.
2. Run `scripts/evaluate_retrieval.py` after any change to ingestion or prompts, to catch retrieval regressions early.
3. The lead-capture conversational flow is driven entirely by `intent` being `"pricing"` or `"contact_request"` — there's no dedicated "ready for lead form" signal from the backend, so the frontend infers it from intent. If you add new intents, check `useChatSession.ts`'s `showLeadPrompt` logic.
4. Free-tier API limits (Gemini, Resend) are the most likely source of flaky behavior in testing — check `docs/DEPLOYMENT.md`'s limitations section before assuming it's a code bug.