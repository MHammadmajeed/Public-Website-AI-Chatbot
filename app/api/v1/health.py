from fastapi import APIRouter

from app.db.session import database_is_healthy

router = APIRouter()


@router.get("/health")
def health_check():
    db_ok = database_is_healthy()
    return {
        "status": "ok" if db_ok else "degraded",
        "app": "ok",
        "database": "ok" if db_ok else "unreachable",
    }