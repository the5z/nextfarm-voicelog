from pathlib import Path
import subprocess
import uuid

from app.utils.logger import logger


def reduce_noise(audio_path: Path) -> Path:
    """
    Reduce background noise and normalize audio before Whisper processing.

    Returns the path to a cleaned WAV file.
    """

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    output_path = audio_path.with_name(
        f"{audio_path.stem}_clean_{uuid.uuid4().hex[:8]}.wav"
    )

    audio_filter = (
        "highpass=f=80,"
        "lowpass=f=8000,"
        "afftdn=nr=12"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-af",
        audio_filter,
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]

    logger.info(
        "Audio noise reduction started | input=%s | output=%s",
        audio_path,
        output_path,
    )

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError as exc:
        logger.exception("FFmpeg executable was not found")

        raise RuntimeError(
            "FFmpeg is not installed or is not available in PATH."
        ) from exc

    except subprocess.CalledProcessError as exc:
        logger.error(
            "FFmpeg noise reduction failed | stderr=%s",
            exc.stderr,
        )

        raise RuntimeError(
            f"FFmpeg noise reduction failed: {exc.stderr}"
        ) from exc

    if not output_path.exists():
        raise RuntimeError(
            "FFmpeg completed but the cleaned audio file was not created."
        )

    logger.info(
        "Audio noise reduction completed | output=%s",
        output_path,
    )

    return output_path