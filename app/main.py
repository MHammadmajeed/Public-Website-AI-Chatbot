from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import chat, health, leads, sessions
from app.core.config import get_settings

from app.logging_config import app_logger, configure_logging

configure_logging()

settings = get_settings()

# Per-IP rate limiting (task 6.7). Keyed by remote address, since this
# is a public-facing widget with no user accounts.
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title="MoinSystems AI Chatbot API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


MAX_BODY_SIZE = 100_000  # 100 KB - generous for chat/lead JSON payloads


@app.middleware("http")
async def limit_body_size(request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)



@app.middleware("http")
async def log_requests(request, call_next):
    import time
    import uuid

    request_id = str(uuid.uuid4())[:8]
    start = time.monotonic()
    response = await call_next(request)
    latency_ms = round((time.monotonic() - start) * 1000, 1)

    app_logger.info(
        "request_completed",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(leads.router, prefix="/api/v1/lead-capture", tags=["leads"])


@app.get("/")
def root():
    return {"service": "moin-ai-chatbot", "status": "running"}