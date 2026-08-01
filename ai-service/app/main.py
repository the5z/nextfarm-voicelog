from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers import audio, health


app = FastAPI(
    title=settings.APP_NAME,
)

# Register global exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(health.router)
app.include_router(audio.router)