import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dynamic_form import (
    HarvestResponse,
    WorkLogResponse,
)


client = TestClient(app)


def build_work_log_response() -> WorkLogResponse:
    return WorkLogResponse(
        missing_fields=[],
        warnings=[],
        field_confidence={
            "result_status": 1.0,
            "plot_text": 1.0,
            "activity_text": 1.0,
            "performed_time_text": 1.0,
        },
        requires_confirmation=False,
        next_question=None,
        fields={
            "result_status": "completed",
            "plot_text": "A1",
            "activity_text": "Bón NPK",
            "performed_time_text": "8 giờ",
            "materials": [
                {
                    "material_text": "NPK",
                    "quantity": 20,
                    "unit_text": "kg",
                }
            ],
            "photo_required": None,
            "material_batch_text": None,
            "note": None,
        },
    )


def build_harvest_response() -> HarvestResponse:
    return HarvestResponse(
        missing_fields=[],
        warnings=[],
        field_confidence={
            "plot_text": 1.0,
            "crop_text": 1.0,
            "quantity": 1.0,
            "unit_text": 1.0,
            "harvest_date_text": 1.0,
        },
        requires_confirmation=False,
        next_question=None,
        fields={
            "plot_text": "A1",
            "crop_text": "lúa",
            "quantity": 120,
            "unit_text": "kg",
            "harvest_date_text": "hôm nay",
            "photo_required": None,
            "note": None,
        },
    )


def test_upload_rejects_invalid_file_type() -> None:
    fake_file = BytesIO(b"fake image content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "test.png",
                fake_file,
                "image/png",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Only MP3, WAV, M4A, OGG, and WEBM "
        "audio files are allowed."
    )
    assert body["data"] is None
    assert "request_id" in body


def test_upload_requires_file() -> None:
    response = client.post(
        "/api/v1/audio/upload"
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Request validation failed."
    )
    assert "errors" in body["data"]
    assert "request_id" in body


def test_upload_audio_success(mocker) -> None:
    transcript = (
        "Bón NPK cho lô A1, dùng 20 ký, "
        "lúc 8 giờ, đã hoàn thành."
    )

    cleaned_path = Path(
        "uploads/cleaned-fertilizing.wav"
    )

    mocker.patch(
        "app.routers.audio.reduce_noise",
        return_value=cleaned_path,
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocked_extract = mocker.patch(
        "app.routers.audio.extract_dynamic_form",
        return_value=build_work_log_response(),
    )

    fake_audio = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "fertilizing.m4a",
                fake_audio,
                "audio/x-m4a",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == (
        "Audio processed successfully."
    )

    data = body["data"]

    assert data["original_filename"] == (
        "fertilizing.m4a"
    )
    assert data["stored_filename"].endswith(
        ".m4a"
    )
    assert data["content_type"] == (
        "audio/x-m4a"
    )
    assert data["operation"] == (
        "CREATE_WORK_LOG"
    )
    assert data["transcript"] == transcript
    assert (
        data["noise_reduction_applied"]
        is True
    )

    dynamic_form = data["dynamic_form"]

    assert dynamic_form["contract_version"] == (
        "3.1"
    )
    assert dynamic_form["operation"] == (
        "CREATE_WORK_LOG"
    )
    assert dynamic_form["template_id"] == (
        "work_log"
    )
    assert dynamic_form["missing_fields"] == []
    assert (
        dynamic_form["requires_confirmation"]
        is False
    )

    fields = dynamic_form["fields"]

    assert fields["plot_text"] == "A1"
    assert fields["activity_text"] == (
        "Bón NPK"
    )
    assert fields["result_status"] == (
        "completed"
    )
    assert fields["performed_time_text"] == (
        "8 giờ"
    )

    materials = fields["materials"]

    assert len(materials) == 1
    assert materials[0]["material_text"] == (
        "NPK"
    )
    assert materials[0]["quantity"] == 20
    assert materials[0]["unit_text"] == "kg"

    mocked_extract.assert_called_once()

    kwargs = mocked_extract.call_args.kwargs

    assert kwargs["operation"] == (
        "CREATE_WORK_LOG"
    )
    assert kwargs["transcript"] == transcript
    assert kwargs["current_fields"] is None
    assert kwargs["context"] is None


def test_upload_passes_operation_to_dynamic_form(
    mocker,
) -> None:
    transcript = (
        "Thu hoạch lúa ở lô A1 "
        "được 120 kg hôm nay."
    )

    mocker.patch(
        "app.routers.audio.reduce_noise",
        return_value=Path(
            "uploads/cleaned-harvest.wav"
        ),
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocked_extract = mocker.patch(
        "app.routers.audio.extract_dynamic_form",
        return_value=build_harvest_response(),
    )

    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "operation": "CREATE_HARVEST",
        },
        files={
            "file": (
                "harvest.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert data["operation"] == (
        "CREATE_HARVEST"
    )

    assert (
        data["dynamic_form"]["operation"]
        == "CREATE_HARVEST"
    )

    kwargs = mocked_extract.call_args.kwargs

    assert kwargs["operation"] == (
        "CREATE_HARVEST"
    )
    assert kwargs["transcript"] == transcript


def test_upload_passes_current_fields_and_context(
    mocker,
) -> None:
    transcript = "20 ký."

    current_fields = {
        "result_status": "completed",
        "plot_text": "A1",
        "activity_text": "Bón NPK",
        "materials": [
            {
                "material_text": "NPK",
                "quantity": None,
                "unit_text": None,
            }
        ],
    }

    context = {
        "plot_text": "A1",
    }

    mocker.patch(
        "app.routers.audio.reduce_noise",
        return_value=Path(
            "uploads/cleaned-follow-up.wav"
        ),
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocked_extract = mocker.patch(
        "app.routers.audio.extract_dynamic_form",
        return_value=build_work_log_response(),
    )

    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "operation": "CREATE_WORK_LOG",
            "current_fields": json.dumps(
                current_fields
            ),
            "context": json.dumps(context),
        },
        files={
            "file": (
                "follow-up.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    kwargs = mocked_extract.call_args.kwargs

    assert kwargs["current_fields"] == (
        current_fields
    )
    assert kwargs["context"] == context


def test_upload_without_noise_reduction(
    mocker,
) -> None:
    transcript = "Đã hoàn thành."

    mocked_reduce_noise = mocker.patch(
        "app.routers.audio.reduce_noise"
    )

    mocked_transcribe = mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocker.patch(
        "app.routers.audio.extract_dynamic_form",
        return_value=build_work_log_response(),
    )

    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "use_noise_reduction": "false",
        },
        files={
            "file": (
                "work.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()["data"]

    assert (
        data["noise_reduction_applied"]
        is False
    )

    mocked_reduce_noise.assert_not_called()
    mocked_transcribe.assert_called_once()


def test_upload_rejects_empty_transcript(
    mocker,
) -> None:
    mocker.patch(
        "app.routers.audio.reduce_noise",
        return_value=Path(
            "uploads/cleaned-empty.wav"
        ),
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value="   ",
    )

    mocked_extract = mocker.patch(
        "app.routers.audio.extract_dynamic_form"
    )

    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "empty.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Could not detect speech in the audio."
    )

    mocked_extract.assert_not_called()


def test_upload_rejects_invalid_current_fields_json() -> None:
    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "current_fields": "{invalid-json",
        },
        files={
            "file": (
                "test.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "current_fields must be valid JSON object."
    )


def test_upload_rejects_non_object_current_fields() -> None:
    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "current_fields": "[]",
        },
        files={
            "file": (
                "test.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["message"] == (
        "current_fields must be valid JSON object."
    )


def test_upload_rejects_invalid_context_json() -> None:
    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "context": "{invalid-json",
        },
        files={
            "file": (
                "test.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "context must be valid JSON object."
    )


def test_upload_rejects_non_object_context() -> None:
    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "context": "[]",
        },
        files={
            "file": (
                "test.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["message"] == (
        "context must be valid JSON object."
    )


def test_upload_rejects_invalid_operation() -> None:
    fake_audio = BytesIO(
        b"fake audio content"
    )

    response = client.post(
        "/api/v1/audio/upload",
        data={
            "operation": "INVALID_OPERATION",
        },
        files={
            "file": (
                "test.wav",
                fake_audio,
                "audio/wav",
            )
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    assert body["message"] == (
        "Request validation failed."
    )