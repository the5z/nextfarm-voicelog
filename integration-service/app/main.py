from fastapi import FastAPI

from app.routers.cultivation_logs import (
    router as cultivation_logs_router,
)
from app.routers.master_data import (
    router as master_data_router,
)
from app.routers.nextfarm import (
    router as nextfarm_router,
)
from app.routers.sync import (
    router as sync_router,
)


app = FastAPI(
    title="NextFarm VoiceLog Integration Service",
    description=(
        "Kiểm tra, lưu, đồng bộ nhật ký canh tác "
        "và tích hợp dữ liệu với NextFarm."
    ),
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
app.include_router(master_data_router)
app.include_router(sync_router)
app.include_router(nextfarm_router)