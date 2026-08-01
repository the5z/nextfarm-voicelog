from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["Health"],
)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-service",
        "version": "1.0.0",
    }