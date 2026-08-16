import asyncio
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import audio, bot, health
from app.utils.logger import logger


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


# Add request ID, request timing, and timeout protection
@app.middleware("http")
async def request_tracking_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid4()),
    )

    request.state.request_id = request_id

    start_time = time.perf_counter()

    logger.info(
        "Request started | request_id=%s | method=%s | path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    try:
        response = await asyncio.wait_for(
            call_next(request),
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )

    except asyncio.TimeoutError:
        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        logger.error(
            "Request timeout | request_id=%s | method=%s | "
            "path=%s | timeout_seconds=%.2f | duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            settings.REQUEST_TIMEOUT_SECONDS,
            duration_ms,
        )

        response = JSONResponse(
            status_code=504,
            content={
                "success": False,
                "message": "Request timed out.",
                "data": None,
                "request_id": request_id,
            },
        )

    duration_ms = (
        time.perf_counter() - start_time
    ) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed | request_id=%s | method=%s | path=%s | "
        "status=%s | duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


# Allow frontend to call AI Service
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


# Register global exception handlers
register_exception_handlers(app)


# Register routers
app.include_router(health.router)
app.include_router(audio.router)
app.include_router(bot.router)