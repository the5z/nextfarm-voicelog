from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import audio, health


app = FastAPI(
    title=settings.APP_NAME,
)


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