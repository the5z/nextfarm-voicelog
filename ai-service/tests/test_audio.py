from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.activity import ActivityData, MaterialData


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
    Should return a validation error when the file is missing.
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
    Should upload and process an audio file successfully
    using mocked Whisper and Gemini results.
    """

    transcript = (
        "Bón phân lô A 20 ký NPK lúc 7 giờ sáng."
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocker.patch(
        "app.routers.audio.extract_activity",
        return_value=ActivityData(
            activity_text="Bón phân",
            lot_text="Lô A",
            materials=[
                MaterialData(
                    material_text="NPK",
                    quantity=20,
                    unit_text="kg",
                )
            ],
            time_text="07:00",
        ),
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
    assert body["message"] == "Audio processed successfully."

    data = body["data"]

    assert data["original_filename"] == "fertilizing.m4a"
    assert data["stored_filename"].endswith(".m4a")
    assert data["content_type"] == "audio/x-m4a"
    assert data["transcript"] == transcript

    structured_data = data["structured_data"]

    assert structured_data["activity_text"] == "Bón phân"
    assert structured_data["lot_text"] == "Lô A"
    assert structured_data["time_text"] == "07:00"

    materials = structured_data["materials"]

    assert len(materials) == 1
    assert materials[0]["material_text"] == "NPK"
    assert materials[0]["quantity"] == 20
    assert materials[0]["unit_text"] == "kg"


def test_upload_audio_with_watering_activity(mocker) -> None:
    """
    Should return structured watering data.
    """

    transcript = (
        "Tưới cây lô B 100 lít nước lúc 6 giờ sáng."
    )

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocker.patch(
        "app.routers.audio.extract_activity",
        return_value=ActivityData(
            activity_text="Tưới nước",
            lot_text="Lô B",
            materials=[
                MaterialData(
                    material_text="Nước",
                    quantity=100,
                    unit_text="lít",
                )
            ],
            time_text="06:00",
        ),
    )

    fake_audio = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "watering.m4a",
                fake_audio,
                "audio/x-m4a",
            )
        },
    )

    assert response.status_code == 200

    structured_data = response.json()["data"]["structured_data"]

    assert structured_data["activity_text"] == "Tưới nước"
    assert structured_data["lot_text"] == "Lô B"
    assert structured_data["time_text"] == "06:00"

    materials = structured_data["materials"]

    assert len(materials) == 1
    assert materials[0]["material_text"] == "Nước"
    assert materials[0]["quantity"] == 100
    assert materials[0]["unit_text"] == "lít"


def test_upload_audio_without_materials(mocker) -> None:
    """
    Should return an empty materials list when no material
    is mentioned in the transcript.
    """

    transcript = "Làm cỏ lô A lúc 8 giờ sáng."

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocker.patch(
        "app.routers.audio.extract_activity",
        return_value=ActivityData(
            activity_text="Làm cỏ",
            lot_text="Lô A",
            materials=[],
            time_text="08:00",
        ),
    )

    fake_audio = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "weeding.m4a",
                fake_audio,
                "audio/x-m4a",
            )
        },
    )

    assert response.status_code == 200

    structured_data = response.json()["data"]["structured_data"]

    assert structured_data["activity_text"] == "Làm cỏ"
    assert structured_data["lot_text"] == "Lô A"
    assert structured_data["materials"] == []
    assert structured_data["time_text"] == "08:00"


def test_upload_audio_without_lot_or_time(mocker) -> None:
    """
    Should allow lot_text and time_text to be null.
    """

    transcript = "Thu hoạch xoài."

    mocker.patch(
        "app.routers.audio.transcribe_audio",
        return_value=transcript,
    )

    mocker.patch(
        "app.routers.audio.extract_activity",
        return_value=ActivityData(
            activity_text="Thu hoạch",
            lot_text=None,
            materials=[],
            time_text=None,
        ),
    )

    fake_audio = BytesIO(b"fake audio content")

    response = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "harvesting.m4a",
                fake_audio,
                "audio/x-m4a",
            )
        },
    )

    assert response.status_code == 200

    structured_data = response.json()["data"]["structured_data"]

    assert structured_data["activity_text"] == "Thu hoạch"
    assert structured_data["lot_text"] is None
    assert structured_data["materials"] == []
    assert structured_data["time_text"] is None