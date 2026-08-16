from fastapi import APIRouter

from app.core.config import settings


router = APIRouter(
    prefix=settings.API_PREFIX,
    tags=["Health"],
)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-service",
        "version": settings.APP_VERSION,
    }


@router.get("/ready")
def readiness_check() -> dict:
    return {
        "status": "ready",
        "service": "ai-service",
        "version": settings.APP_VERSION,
        "models": {
            "whisper": settings.WHISPER_MODEL,
            "gemini": settings.GEMINI_MODEL,
        },
        "request_timeout_seconds": settings.REQUEST_TIMEOUT_SECONDS,
    }