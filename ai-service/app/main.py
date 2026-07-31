from fastapi import FastAPI

from app.routers.health import router as health_router

app = FastAPI(
    title="NextFarm VoiceLog AI Service",
    description="AI Service for processing voice logs",
    version="1.0.0",
)

app.include_router(health_router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": "Welcome to NextFarm VoiceLog AI Service"
    }