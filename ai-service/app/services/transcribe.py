from pathlib import Path

import whisper

from app.core.config import settings


MODEL_NAME = settings.WHISPER_MODEL

_model = whisper.load_model(
    MODEL_NAME
)


def transcribe_audio(
    file_path: str | Path,
) -> str:
    audio_path = Path(
        file_path
    )

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    result = _model.transcribe(
        str(audio_path),

        # VoiceLog xử lý tiếng Việt.
        language="vi",

        # Phiên âm, không dịch.
        task="transcribe",

        # Chạy CPU trên máy hiện tại.
        fp16=False,

        # Decode ổn định.
        temperature=0,

        # Beam search để thử nhiều phương án nhận dạng.
        beam_size=5,

        # Giảm nguy cơ transcript bị lặp giữa các đoạn.
        condition_on_previous_text=False,
    )

    return result[
        "text"
    ].strip()