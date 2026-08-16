from pathlib import Path

import whisper

from app.core.config import settings


MODEL_NAME = settings.WHISPER_MODEL

_model = whisper.load_model(MODEL_NAME)


def transcribe_audio(file_path: str | Path) -> str:
    audio_path = Path(file_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    result = _model.transcribe(
        str(audio_path),
        language="vi",
        fp16=False,
    )

    return result["text"].strip()