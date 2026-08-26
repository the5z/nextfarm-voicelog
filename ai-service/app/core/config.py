import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Centralized application configuration.
    """

    # Application
    APP_NAME: str = os.getenv(
        "APP_NAME",
        "NextFarm AI Service",
    )

    APP_VERSION: str = os.getenv(
        "APP_VERSION",
        "1.0.0",
    )

    API_PREFIX: str = os.getenv(
        "API_PREFIX",
        "/api/v1",
    )

    # Gemini
    GEMINI_API_KEY: str = os.getenv(
        "GEMINI_API_KEY",
        "",
    )

    GEMINI_MODEL: str = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    # Whisper
    WHISPER_MODEL: str = os.getenv(
        "WHISPER_MODEL",
        "base",
    )

    WHISPER_LANGUAGE: str = os.getenv(
        "WHISPER_LANGUAGE",
        "vi",
    )

    WHISPER_INITIAL_PROMPT: str = os.getenv(
        "WHISPER_INITIAL_PROMPT",
        (
            "Nhật ký canh tác NextFarm bằng tiếng Việt. "
            "Các từ thường gặp: lô A, lô B, bón phân, "
            "phun thuốc, tưới nước, làm cỏ, thu hoạch, "
            "cho bò ăn, cám, phân NPK, phân urê, "
            "kilogram, kg, gam, lít, chai, bao. "
            "Ví dụ: Cho bò ăn 20 kg cám tại lô A lúc 7 giờ sáng."
        ),
    )

    # File upload
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        "uploads",
    )

    # Production safeguards
    REQUEST_TIMEOUT_SECONDS: float = float(
        os.getenv(
            "REQUEST_TIMEOUT_SECONDS",
            "60",
        )
    )


settings = Settings()