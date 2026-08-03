from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.responses.api_response import ApiResponse
from app.services.llm_service import extract_activity
from app.services.transcribe import transcribe_audio
from app.utils.logger import logger


router = APIRouter(
    prefix="/api/v1/audio",
    tags=["Audio"],
)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
}


@router.post(
    "/upload",
    response_model=ApiResponse,
    responses={
        400: {
            "model": ApiResponse,
            "description": "Invalid audio file.",
        },
        422: {
            "model": ApiResponse,
            "description": "Request validation failed.",
        },
        500: {
            "model": ApiResponse,
            "description": "Internal server error.",
        },
    },
)
async def upload_audio(file: UploadFile = File(...)) -> ApiResponse:
    """
    Upload audio -> Whisper -> Gemini -> AI Text Contract V2
    """

    original_filename = file.filename

    logger.info(
        "Audio upload started | filename=%s | content_type=%s",
        original_filename,
        file.content_type,
    )

    if not original_filename:
        logger.warning("Upload rejected: missing filename")

        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        logger.warning(
            "Upload rejected | unsupported extension=%s | filename=%s",
            extension,
            original_filename,
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Only MP3, WAV, M4A, OGG, and WEBM "
                "audio files are allowed."
            ),
        )

    stored_filename = f"{uuid.uuid4()}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(
            "Audio saved successfully | filename=%s | path=%s",
            stored_filename,
            file_path,
        )

    except Exception:
        logger.exception(
            "Failed to save uploaded file | filename=%s",
            original_filename,
        )
        raise

    finally:
        await file.close()

    logger.info(
        "Whisper transcription started | filename=%s",
        stored_filename,
    )

    transcript = transcribe_audio(file_path)

    logger.info(
        "Whisper transcription completed | transcript=%s",
        transcript,
    )

    logger.info(
        "Gemini extraction started | filename=%s",
        stored_filename,
    )

    structured_data = extract_activity(transcript)

    logger.info(
        (
            "Gemini extraction completed | "
            "activity=%s | lot=%s | materials=%s | time=%s"
        ),
        structured_data.activity_text,
        structured_data.lot_text,
        structured_data.materials,
        structured_data.time_text,
    )

    logger.info(
        "Audio processing completed successfully | filename=%s",
        stored_filename,
    )

    return ApiResponse(
        success=True,
        message="Audio processed successfully.",
        data={
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "content_type": file.content_type,
            "path": str(file_path),
            "transcript": transcript,
            "structured_data": structured_data.model_dump(),
        },
    )