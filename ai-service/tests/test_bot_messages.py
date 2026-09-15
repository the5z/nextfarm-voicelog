from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_session(payload: dict) -> dict:
    response = client.post(
        "/api/v1/bot/sessions",
        json=payload,
    )

    assert response.status_code == 200

    return response.json()


def send_message(
    session_id: str,
    message: str,
) -> dict:
    response = client.post(
        f"/api/v1/bot/sessions/{session_id}/messages",
        json={
            "message": message,
        },
    )

    assert response.status_code == 200

    return response.json()


def test_message_fills_missing_time():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": None,
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    assert session["status"] == "collecting"
    assert session["expected_field"] == "time_text"

    updated = send_message(
        session["session_id"],
        "8 giờ",
    )

    assert updated["collected_data"]["time_text"] == "08:00"
    assert updated["status"] == "completed"
    assert updated["expected_field"] is None
    assert updated["next_question"] is None


def test_message_fills_missing_lot():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": None,
            "materials": [],
            "time_text": "08:00",
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    assert session["expected_field"] == "lot_text"

    updated = send_message(
        session["session_id"],
        "Lô A",
    )

    assert updated["collected_data"]["lot_text"] == "Lô A"
    assert updated["status"] == "completed"


def test_message_fills_quantity_and_unit():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "NPK",
                    "quantity": None,
                    "unit_text": None,
                }
            ],
            "time_text": "08:00",
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    assert (
        session["expected_field"]
        == "materials.quantity"
    )

    updated = send_message(
        session["session_id"],
        "20 kg",
    )

    material = updated["collected_data"]["materials"][0]

    assert material["quantity"] == 20
    assert material["unit_text"] == "kg"
    assert updated["status"] == "completed"
    assert updated["expected_field"] is None


def test_invalid_time_keeps_session_collecting():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": None,
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    updated = send_message(
        session["session_id"],
        "25 giờ",
    )

    assert updated["collected_data"]["time_text"] is None
    assert updated["status"] == "collecting"
    assert updated["expected_field"] == "time_text"


def test_message_fills_material_name():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": None,
                    "quantity": None,
                    "unit_text": None,
                }
            ],
            "time_text": "08:00",
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    assert (
        session["expected_field"]
        == "materials.material_text"
    )

    updated = send_message(
        session["session_id"],
        "NPK",
    )

    material = updated["collected_data"]["materials"][0]

    assert material["material_text"] == "NPK"


def test_message_fills_material_unit():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [
                {
                    "material_text": "NPK",
                    "quantity": 20,
                    "unit_text": None,
                }
            ],
            "time_text": "08:00",
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    assert (
        session["expected_field"]
        == "materials.unit_text"
    )

    updated = send_message(
        session["session_id"],
        "kg",
    )

    material = updated["collected_data"]["materials"][0]

    assert material["unit_text"] == "kg"
    assert updated["status"] == "completed"


def test_empty_message_does_not_change_activity():
    session = create_session(
        {
            "activity_text": "Bón phân",
            "lot_text": "Lô A",
            "materials": [],
            "time_text": None,
            "missing_fields": [],
            "warnings": [],
            "requires_confirmation": False,
        }
    )

    updated = send_message(
        session["session_id"],
        "   ",
    )

    assert updated["collected_data"]["time_text"] is None
    assert updated["status"] == "collecting"
    assert updated["expected_field"] == "time_text"