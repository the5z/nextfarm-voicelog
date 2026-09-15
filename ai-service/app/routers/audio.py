import json
from pathlib import Path
import shutil
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.responses.api_response import ApiResponse
from app.schemas.dynamic_form import OperationType
from app.services.audio_preprocessing import reduce_noise
from app.services.dynamic_form_service import extract_dynamic_form
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
async def upload_audio(
    file: UploadFile = File(...),
    operation: OperationType = Form("CREATE_WORK_LOG"),
    current_fields: str | None = Form(None),
    context: str | None = Form(None),
    use_noise_reduction: bool = Form(True),
) -> ApiResponse:
    """
    Upload audio, transcribe with Whisper, then extract
    Dynamic Form V3.1 fields with Gemini.

    Frontend cũ không gửi operation vẫn hoạt động:
    operation mặc định = CREATE_WORK_LOG.

    current_fields và context được truyền dưới dạng JSON string.
    """

    original_filename = file.filename
    cleaned_audio_path: Path | None = None

    logger.info(
        (
            "Audio upload started | filename=%s | "
            "content_type=%s | operation=%s | "
            "noise_reduction=%s"
        ),
        original_filename,
        file.content_type,
        operation,
        use_noise_reduction,
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

    current_fields_data: dict[str, Any] | None = None
    context_data: dict[str, Any] | None = None

    if current_fields:
        try:
            parsed_current_fields = json.loads(current_fields)

            if not isinstance(parsed_current_fields, dict):
                raise ValueError("current_fields must be a JSON object.")

            current_fields_data = parsed_current_fields

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "Invalid current_fields JSON | error=%s",
                exc,
            )

            raise HTTPException(
                status_code=400,
                detail="current_fields must be valid JSON object.",
            ) from exc

    if context:
        try:
            parsed_context = json.loads(context)

            if not isinstance(parsed_context, dict):
                raise ValueError("context must be a JSON object.")

            context_data = parsed_context

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "Invalid context JSON | error=%s",
                exc,
            )

            raise HTTPException(
                status_code=400,
                detail="context must be valid JSON object.",
            ) from exc

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

    try:
        audio_path_for_whisper = file_path

        # ---------------------------------------------------------
        # 1. Noise reduction
        # ---------------------------------------------------------
        if use_noise_reduction:
            logger.info(
                "Audio preprocessing started | filename=%s",
                stored_filename,
            )

            cleaned_audio_path = reduce_noise(file_path)
            audio_path_for_whisper = cleaned_audio_path

            logger.info(
                "Audio preprocessing completed | cleaned_path=%s",
                cleaned_audio_path,
            )

        else:
            logger.info(
                "Audio preprocessing skipped | filename=%s",
                stored_filename,
            )

        # ---------------------------------------------------------
        # 2. Whisper transcription
        # ---------------------------------------------------------
        logger.info(
            "Whisper transcription started | filename=%s",
            audio_path_for_whisper.name,
        )

        transcript = transcribe_audio(audio_path_for_whisper)

        logger.info(
            "Whisper transcription completed | transcript=%s",
            transcript,
        )

        if not transcript.strip():
            logger.warning(
                "Whisper returned empty transcript | filename=%s",
                stored_filename,
            )

            raise HTTPException(
                status_code=400,
                detail="Could not detect speech in the audio.",
            )

        # ---------------------------------------------------------
        # 3. Dynamic Form V3.1 extraction
        # ---------------------------------------------------------
        logger.info(
            (
                "Dynamic Form extraction started | "
                "operation=%s | filename=%s"
            ),
            operation,
            stored_filename,
        )

        dynamic_form = extract_dynamic_form(
            operation=operation,
            transcript=transcript,
            current_fields=current_fields_data,
            context=context_data,
        )

        logger.info(
            (
                "Dynamic Form extraction completed | "
                "operation=%s | template_id=%s | "
                "missing=%s | warnings=%s | "
                "requires_confirmation=%s"
            ),
            operation,
            dynamic_form.template_id,
            dynamic_form.missing_fields,
            dynamic_form.warnings,
            dynamic_form.requires_confirmation,
        )

        # ---------------------------------------------------------
        # 4. API response
        # ---------------------------------------------------------
        return ApiResponse(
            success=True,
            message="Audio processed successfully.",
            data={
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "content_type": file.content_type,
                "path": str(file_path),
                "noise_reduction_applied": use_noise_reduction,
                "operation": operation,
                "transcript": transcript,
                "dynamic_form": dynamic_form.model_dump(),
            },
        )

    finally:
        # ---------------------------------------------------------
        # 5. Delete temporary cleaned audio
        # ---------------------------------------------------------
        if (
            cleaned_audio_path is not None
            and cleaned_audio_path.exists()
        ):
            try:
                cleaned_audio_path.unlink()

                logger.info(
                    "Temporary cleaned audio deleted | path=%s",
                    cleaned_audio_path,
                )

            except OSError:
                logger.exception(
                    "Failed to delete temporary cleaned audio | path=%s",
                    cleaned_audio_path,
                )