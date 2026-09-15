from pathlib import Path
import re

import whisper

from app.core.config import settings
from app.services.transcript_correction import (
    correct_transcript,
)
from app.utils.logger import logger


MODEL_NAME = settings.WHISPER_MODEL

_model = whisper.load_model(
    MODEL_NAME
)


def has_excessive_repetition(
    text: str,
) -> bool:
    if not text:
        return False

    pattern = re.compile(
        r"""
        (
            \b[^\W\d_]+\b
        )
        (?:
            [\s,.;:!?]+
            \1
        ){3,}
        """,
        flags=(
            re.IGNORECASE
            | re.VERBOSE
        ),
    )

    return bool(
        pattern.search(text)
    )


def transcribe_audio(
    file_path: str | Path,
) -> str:
    audio_path = Path(
        file_path
    )

    if not audio_path.exists():
        raise FileNotFoundError(
            (
                "Audio file not found: "
                f"{audio_path}"
            )
        )

    logger.info(
        (
            "Whisper transcribe start | "
            "model=%s | language=%s | "
            "file=%s"
        ),
        MODEL_NAME,
        settings.WHISPER_LANGUAGE,
        audio_path,
    )

    result = _model.transcribe(
        str(audio_path),

        language=(
            settings.WHISPER_LANGUAGE
        ),

        task="transcribe",

        initial_prompt=settings.WHISPER_INITIAL_PROMPT,

        fp16=False,

        temperature=0,

        beam_size=5,

        condition_on_previous_text=False,
    )

    raw_text = str(
        result.get(
            "text",
            "",
        )
    ).strip()

    logger.info(
        (
            "Whisper raw transcript | "
            "text=%s"
        ),
        raw_text,
    )

    if has_excessive_repetition(
        raw_text
    ):
        logger.warning(
            (
                "Whisper pathological "
                "repetition detected | "
                "text=%s"
            ),
            raw_text,
        )

    candidate_text = (
        raw_text
    )

    logger.info(
        (
            "Whisper transcript "
            "passed to correction | "
            "text=%s"
        ),
        candidate_text,
    )

    corrected_text = (
        correct_transcript(
            candidate_text
        )
    )

    logger.info(
        (
            "Transcript after "
            "correction | text=%s"
        ),
        corrected_text,
    )

    return corrected_text