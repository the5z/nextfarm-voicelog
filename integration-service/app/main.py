from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.routers.history import (
    router as history_router,
)
from app.routers.issue_reports import (
    router as issue_reports_router,
)
from app.routers.tasks import (
    router as tasks_router,
)
from app.routers.harvests import (
    router as harvests_router,
)
from app.routers.seasons import (
    router as seasons_router,
)
from app.routers.crop_types import (
    router as crop_types_router,
)
app = FastAPI(
    title="NextFarm VoiceLog Integration Service",
    description=(
        "Kiểm tra, lưu, đồng bộ nhật ký canh tác "
        "và tích hợp dữ liệu với NextFarm."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(history_router)
app.include_router(issue_reports_router)
app.include_router(tasks_router)
app.include_router(harvests_router)
app.include_router(seasons_router)
app.include_router(crop_types_router)