from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.transcribe import transcribe_audio
from app.services.llm_service import extract_activity


router = APIRouter(
    prefix="/api/v1/audio",
    tags=["Audio"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".ogg",
    ".webm",
}


@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    original_filename = file.filename

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="File name is missing.",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only MP3, WAV, M4A, OGG, and WEBM audio files are allowed.",
        )

    stored_filename = f"{uuid.uuid4()}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # Speech-to-Text
    transcript = transcribe_audio(file_path)

    # Mock LLM (sẽ thay bằng LLM thật ở bước sau)
    structured_data = extract_activity(transcript)

    return {
        "success": True,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": file.content_type,
        "path": str(file_path),
        "transcript": transcript,
        "structured_data": structured_data.model_dump(),
    }