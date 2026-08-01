from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.activity import ActivityData


client = TestClient(app)


def test_upload_rejects_invalid_file_type() -> None:
    """
    Should reject non-audio files.
    """

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


def test_upload_requires_file() -> None:
    """
    Should return validation error when file is missing.
    """

    response = client.post(
        "/api/v1/audio/upload"
    )

    assert response.status_code == 422

    body = response.json()

    assert body["success"] is False
    assert body["message"] == "Request validation failed."
    assert "errors" in body["data"]


def test_upload_audio_success(mocker) -> None:
    """
    Should upload audio successfully using mocked Whisper and Gemini.
    """

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value="Cho bò ăn 20 ký cám lúc 7 giờ sáng.",
    )

    mocker.patch(
        "app.routers.audio.extract_activity",
        return_value=ActivityData(
            activity="feeding",
            animal="cow",
            quantity=20,
            unit="kg",
            time="07:00",
            note="ký cám",
        ),
    )

    fake_audio = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "sample.m4a",
                fake_audio,
                "audio/x-m4a",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["message"] == "Audio processed successfully."

    data = body["data"]

    assert data["original_filename"] == "sample.m4a"
    assert data["stored_filename"].endswith(".m4a")
    assert data["content_type"] == "audio/x-m4a"
    assert data["transcript"] == (
        "Cho bò ăn 20 ký cám lúc 7 giờ sáng."
    )

    structured_data = data["structured_data"]

    assert structured_data["activity"] == "feeding"
    assert structured_data["animal"] == "cow"
    assert structured_data["quantity"] == 20
    assert structured_data["unit"] == "kg"
    assert structured_data["time"] == "07:00"
    assert structured_data["note"] == "ký cám"