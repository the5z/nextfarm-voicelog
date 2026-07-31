from fastapi import FastAPI

from app.routers.cultivation_logs import router as cultivation_logs_router


app = FastAPI(
    title="NextFarm VoiceLog Integration Service",
    version="0.1.0",
)


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "NextFarm VoiceLog Integration Service",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "integration-service",
        "version": "0.1.0",
    }


app.include_router(cultivation_logs_router)