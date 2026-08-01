import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Centralized application configuration.
    """

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    GEMINI_MODEL: str = "gemini-3.1-flash-lite"

    UPLOAD_DIR: str = "uploads"

    API_PREFIX: str = "/api/v1"

    APP_NAME: str = "NextFarm AI Service"


settings = Settings()