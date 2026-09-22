from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chat, health, leads, sessions
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="MoinSystems AI Chatbot API", version="0.1.0")

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