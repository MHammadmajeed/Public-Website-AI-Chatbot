# Deployment & Rollback Guide — MoinSystems AI Chatbot

## Architecture overview

- **Backend**: FastAPI (Python 3.14), hosted as a Render Web Service
- **Database**: Neon (managed PostgreSQL + pgvector), **not** Render Postgres
- **LLM / Embeddings**: Google Gemini (`gemini-3.8-flash` for chat, `gemini-embedding-001` for retrieval)
- **Email**: Resend (free tier — can only send to the address the account was signed up with; see `LEAD_EMAIL_DEV_TO` note below)
- **Frontend widget**: React + TypeScript (Vite), in `frontend/` — deployed separately from the backend (see "Frontend deployment" below)

## Prerequisites

- A Neon account with the production database already provisioned and pgvector enabled
- A Render account (free tier Web Service — no card required for this part)
- API keys ready: `GEMINI_API_KEY`, `RESEND_API_KEY`
- This repo pushed to GitHub (Render deploys from a connected GitHub repo)

## Environment variables (set in Render dashboard, NOT in a committed file)

| Variable | Example / Notes |
|---|---|
| `APP_ENV` | `production` |
| `APP_URL` | `https://<your-render-service>.onrender.com` |
| `ALLOWED_ORIGINS` | Comma-separated list, must include the **production frontend URL** once the widget is hosted somewhere |
| `APP_SECRET` | A long random string (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `DATABASE_URL` | Your Neon connection string, in `postgresql+psycopg://...` format |
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | From Google AI Studio |
| `EMBEDDING_MODEL` | `gemini-embedding-001` |
| `EMAIL_PROVIDER` | `resend` |
| `RESEND_API_KEY` | From Resend dashboard |
| `LEAD_EMAIL_TO` | `info@moinsystemsai.com` |
| `LEAD_EMAIL_DEV_TO` | Leave **blank** in production (this only applies when `APP_ENV=local`) |
| `RATE_LIMIT` | `60/minute` |
| `RETRIEVAL_TOP_K` | `5` |
| `RETRIEVAL_THRESHOLD` | `0.55` |

**Never commit a real `.env` file.** `.gitignore` already excludes it — confirmed via `git log --all --full-history -- .env` returning no results (never committed).

## Deployment steps (Render)

1. Log into Render, click **New +** → **Web Service**.
2. Connect the GitHub repo (`MHammadmajeed/Public-Website-AI-Chatbot`).
3. Configure:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/`
4. Add every environment variable from the table above under the service's **Environment** tab.
5. Deploy. Watch the build logs for errors (most likely cause of failure: a missing env var or a `requirements.txt` install error).
6. Once live, verify:

   Should return `{"service":"moin-ai-chatbot","status":"running"}`.

## Post-deploy smoke test checklist

- [ ] Health check returns 200
- [ ] `POST /api/v1/sessions` creates a session
- [ ] `POST /api/v1/chat/messages` returns a grounded response (test a `general`, a `pricing`, and a `services` question)
- [ ] `POST /api/v1/lead-capture` saves a lead and the email arrives at `info@moinsystemsai.com`
- [ ] CORS allows requests from the actual frontend origin (test from the deployed widget, not just `curl`)
- [ ] Rate limiting triggers correctly past the configured limit (both chat and lead-capture endpoints)

## Rollback procedure

Render keeps a history of previous deploys.

1. Go to the Render dashboard → your service → **Events** (or **Deploys**) tab.
2. Find the last known-good deploy (identified by its commit hash/message).
3. Click **Rollback to this deploy** (or redeploy that specific commit manually if the option isn't directly available).
4. Re-run the smoke test checklist above against the rolled-back version to confirm it's healthy.
5. If the rollback was due to a bad environment variable (not code), you can instead just fix the variable in the Render dashboard and trigger a redeploy of the current commit — no code rollback needed.

**Database rollback note**: since Neon is separate from the app deploy, a bad backend deploy does **not** require a database rollback unless a migration was involved. If a migration *was* part of the bad deploy, check `alembic history` and run `alembic downgrade -1` against the production `DATABASE_URL` before rolling back the app code.

## Known limitations (documented, not bugs)

- **Gemini free tier**: occasionally returns `503 Service Unavailable` under load. The backend retries with exponential backoff (2s → 5s → 10s), which can occasionally still exceed a client's timeout on a bad day. This is an external API limitation, not a defect in this codebase.
- **Resend free tier**: can only send to the email address the Resend account was registered with. Production lead emails to `info@moinsystemsai.com` require either upgrading the Resend plan or verifying a sending domain.
- **RAG retrieval**: 84.4% Top-5 accuracy (27/32) as of the latest evaluation (`eval_report_day8.txt`). Failures are near-misses between semantically similar FAQ/service records, not retrieval failures in the traditional sense — see the report for details.

## Frontend deployment (separate from backend)

The React widget (`frontend/`) is not deployed as part of this backend service. To deploy it:

1. `cd frontend && npm run build` — produces a static bundle in `frontend/dist`.
2. Host that static bundle anywhere (Netlify, Vercel, GitHub Pages, or alongside the main MoinSystems website).
3. Once hosted, update the backend's `ALLOWED_ORIGINS` environment variable in Render to include that URL, and redeploy.
4. Update `frontend/.env`'s `VITE_API_BASE_URL` to point at the deployed Render backend URL before building.