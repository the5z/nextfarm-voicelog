from copy import deepcopy
from typing import Any

from fastapi.testclient import TestClient


def build_valid_log(
    client_record_id: str = "test-log-001",
) -> dict[str, Any]:
    """
    Tạo một bản ghi nhật ký hợp lệ dùng chung cho các bài test.
    """

    return {
        "schema_version": "1.0",
        "client_record_id": client_record_id,
        "transcript": "Bón 20 kg NPK cho lô A",
        "lot_code": "LO_A",
        "activity_code": "BON_PHAN",
        "materials": [
            {
                "material_code": "NPK",
                "quantity": 20,
                "unit_code": "KG",
            }
        ],
        "performed_at": "2026-08-02T07:00:00+07:00",
        "performer_code": "NV001",
        "notes": "Bón phân lần một",
        "source": "voice",
        "confirmed": True,
    }


def test_save_confirmed_log(
    client: TestClient,
) -> None:
    """
    Nhật ký đã xác nhận phải được lưu thành công.
    """

    payload = build_valid_log()

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["success"] is True
    assert response_data["status"] == "saved"

    stored_log = response_data["data"]

    assert stored_log["client_record_id"] == "test-log-001"
    assert stored_log["lot_code"] == "LO_A"
    assert stored_log["activity_code"] == "BON_PHAN"
    assert stored_log["confirmed"] is True
    assert stored_log["status"] == "saved"

    assert len(stored_log["materials"]) == 1
    assert (
        stored_log["materials"][0]["material_code"]
        == "NPK"
    )
    assert stored_log["materials"][0]["quantity"] == 20
    assert stored_log["materials"][0]["unit_code"] == "KG"


def test_reject_unconfirmed_log(
    client: TestClient,
) -> None:
    """
    Nhật ký chưa xác nhận không được lưu vào database.
    """

    payload = build_valid_log(
        client_record_id="test-unconfirmed-001"
    )

    payload["confirmed"] = False

    response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "UNCONFIRMED_RECORD"
    )

    list_response = client.get(
        "/api/cultivation-logs"
    )

    assert list_response.status_code == 200
    assert list_response.json()["data"] == []


def test_prevent_duplicate_record(
    client: TestClient,
) -> None:
    """
    Gửi lại cùng client_record_id không được tạo bản ghi mới.
    """

    payload = build_valid_log(
        client_record_id="test-duplicate-001"
    )

    first_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["status"] == "saved"
    assert second_data["status"] == "already_exists"

    assert (
        first_data["data"]["id"]
        == second_data["data"]["id"]
    )

    list_response = client.get(
        "/api/cultivation-logs"
    )

    stored_logs = list_response.json()["data"]

    assert len(stored_logs) == 1


def test_list_saved_logs(
    client: TestClient,
) -> None:
    """
    API danh sách phải trả về các nhật ký đã lưu.
    """

    first_payload = build_valid_log(
        client_record_id="test-list-001"
    )

    second_payload = deepcopy(first_payload)
    second_payload["client_record_id"] = "test-list-002"
    second_payload["lot_code"] = "LO_B"
    second_payload["transcript"] = (
        "Tưới nước cho lô B"
    )
    second_payload["activity_code"] = "TUOI_NUOC"
    second_payload["materials"] = []

    first_response = client.post(
        "/api/cultivation-logs",
        json=first_payload,
    )

    second_response = client.post(
        "/api/cultivation-logs",
        json=second_payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        "/api/cultivation-logs"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is True
    assert len(response_data["data"]) == 2

    client_record_ids = {
        record["client_record_id"]
        for record in response_data["data"]
    }

    assert client_record_ids == {
        "test-list-001",
        "test-list-002",
    }

def test_get_saved_log_detail(
    client: TestClient,
) -> None:
    """
    Có thể lấy lại chi tiết nhật ký bằng client_record_id.
    """

    payload = build_valid_log(
        client_record_id="test-detail-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    response = client.get(
        "/api/cultivation-logs/test-detail-001"
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["success"] is True

    stored_log = response_data["data"]

    assert stored_log["client_record_id"] == "test-detail-001"
    assert stored_log["lot_code"] == "LO_A"
    assert stored_log["activity_code"] == "BON_PHAN"
    assert stored_log["confirmed"] is True
    assert stored_log["status"] == "saved"


def test_get_saved_log_detail_includes_materials(
    client: TestClient,
) -> None:
    """
    API chi tiết phải trả về đầy đủ vật tư của nhật ký.
    """

    payload = build_valid_log(
        client_record_id="test-detail-materials-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    response = client.get(
        "/api/cultivation-logs/test-detail-materials-001"
    )

    assert response.status_code == 200

    stored_log = response.json()["data"]

    assert len(stored_log["materials"]) == 1

    material = stored_log["materials"][0]

    assert material["material_code"] == "NPK"
    assert material["quantity"] == 20
    assert material["unit_code"] == "KG"


def test_get_log_detail_not_found(
    client: TestClient,
) -> None:
    """
    client_record_id không tồn tại phải trả về HTTP 404.
    """

    response = client.get(
        "/api/cultivation-logs/not-found-001"
    )

    assert response.status_code == 404

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "CULTIVATION_LOG_NOT_FOUND"
    )

    assert response_data["detail"]["message"] == (
        "Không tìm thấy nhật ký."
    )

def test_update_saved_log_quantity(
    client: TestClient,
) -> None:
    """
    Có thể cập nhật số lượng của một nhật ký
    đã tồn tại.
    """

    payload = build_valid_log(
        client_record_id="test-update-quantity-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)
    update_payload["transcript"] = (
        "Bón 18 kg NPK cho lô A"
    )
    update_payload["materials"][0]["quantity"] = 18

    # Gửi yêu cầu cập nhật thật lên backend.
    update_response = client.put(
        "/api/cultivation-logs/"
        "test-update-quantity-001",
        json=update_payload,
    )

    assert update_response.status_code == 200

    updated_log = update_response.json()["data"]

    assert updated_log["materials"][0]["quantity"] == 18

    # Kiểm tra dữ liệu thực sự đã persist vào database.
    detail_response = client.get(
        "/api/cultivation-logs/"
        "test-update-quantity-001"
    )

    assert detail_response.status_code == 200

    stored_log = detail_response.json()["data"]

    assert stored_log["materials"][0]["quantity"] == 18


def test_update_saved_log_preserves_multiple_materials(
    client: TestClient,
) -> None:
    """
    Update một nhật ký có nhiều vật tư phải giữ
    đầy đủ materials[].
    """

    payload = build_valid_log(
        client_record_id="test-update-materials-001"
    )

    payload["transcript"] = (
        "Bón 20 kg NPK và 10 kg phân urê cho lô A"
    )

    payload["materials"] = [
        {
            "material_code": "NPK",
            "quantity": 20,
            "unit_code": "KG",
        },
        {
            "material_code": "URE",
            "quantity": 10,
            "unit_code": "KG",
        },
    ]

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["transcript"] = (
        "Bón 18 kg NPK và 12 kg phân urê cho lô A"
    )

    update_payload["materials"][0]["quantity"] = 18
    update_payload["materials"][1]["quantity"] = 12

    update_response = client.put(
        "/api/cultivation-logs/"
        "test-update-materials-001",
        json=update_payload,
    )

    assert update_response.status_code == 200

    response_data = update_response.json()

    assert response_data["success"] is True
    assert response_data["status"] == "updated"

    updated_log = response_data["data"]

    assert len(updated_log["materials"]) == 2

    materials = {
        material["material_code"]: material
        for material in updated_log["materials"]
    }

    assert materials["NPK"]["quantity"] == 18
    assert materials["NPK"]["unit_code"] == "KG"

    assert materials["URE"]["quantity"] == 12
    assert materials["URE"]["unit_code"] == "KG"


def test_update_saved_log_replaces_materials(
    client: TestClient,
) -> None:
    """
    PUT gửi materials[] mới phải thay thế danh sách
    vật tư cũ, không giữ lại child rows cũ.
    """

    payload = build_valid_log(
        client_record_id="test-update-replace-materials-001"
    )

    payload["materials"] = [
        {
            "material_code": "NPK",
            "quantity": 20,
            "unit_code": "KG",
        },
        {
            "material_code": "URE",
            "quantity": 10,
            "unit_code": "KG",
        },
    ]

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)

    update_payload["materials"] = [
        {
            "material_code": "NPK",
            "quantity": 18,
            "unit_code": "KG",
        }
    ]

    update_response = client.put(
        "/api/cultivation-logs/"
        "test-update-replace-materials-001",
        json=update_payload,
    )

    assert update_response.status_code == 200

    updated_log = update_response.json()["data"]

    assert len(updated_log["materials"]) == 1
    assert (
        updated_log["materials"][0]["material_code"]
        == "NPK"
    )
    assert updated_log["materials"][0]["quantity"] == 18


def test_update_log_not_found(
    client: TestClient,
) -> None:
    """
    Update một client_record_id không tồn tại
    phải trả về HTTP 404.
    """

    payload = build_valid_log(
        client_record_id="test-update-not-found-001"
    )

    response = client.put(
        "/api/cultivation-logs/"
        "test-update-not-found-001",
        json=payload,
    )

    assert response.status_code == 404

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "CULTIVATION_LOG_NOT_FOUND"
    )


def test_update_log_rejects_unconfirmed(
    client: TestClient,
) -> None:
    """
    Không được update nhật ký nếu confirmed=False.
    """

    payload = build_valid_log(
        client_record_id="test-update-unconfirmed-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)
    update_payload["confirmed"] = False
    update_payload["materials"][0]["quantity"] = 18

    response = client.put(
        "/api/cultivation-logs/"
        "test-update-unconfirmed-001",
        json=update_payload,
    )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "UNCONFIRMED_RECORD"
    )

    # Database phải giữ nguyên dữ liệu cũ.
    detail_response = client.get(
        "/api/cultivation-logs/"
        "test-update-unconfirmed-001"
    )

    assert detail_response.status_code == 200

    stored_log = detail_response.json()["data"]

    assert stored_log["materials"][0]["quantity"] == 20


def test_update_log_rejects_client_record_id_mismatch(
    client: TestClient,
) -> None:
    """
    client_record_id trong URL và body phải giống nhau.
    """

    payload = build_valid_log(
        client_record_id="test-update-body-id-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)
    update_payload["client_record_id"] = (
        "test-update-another-id-001"
    )
    update_payload["materials"][0]["quantity"] = 18

    response = client.put(
        "/api/cultivation-logs/"
        "test-update-body-id-001",
        json=update_payload,
    )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "CLIENT_RECORD_ID_MISMATCH"
    )

    # Record gốc phải không đổi.
    detail_response = client.get(
        "/api/cultivation-logs/"
        "test-update-body-id-001"
    )

    assert detail_response.status_code == 200

    stored_log = detail_response.json()["data"]

    assert stored_log["materials"][0]["quantity"] == 20


def test_update_log_rejects_invalid_business_rule(
    client: TestClient,
) -> None:
    """
    Business validation phải được chạy lại khi update.

    BON_PHAN bắt buộc có material theo rule hiện tại,
    nên update thành materials=[] phải bị từ chối.
    """

    payload = build_valid_log(
        client_record_id="test-update-business-rule-001"
    )

    save_response = client.post(
        "/api/cultivation-logs",
        json=payload,
    )

    assert save_response.status_code == 201

    update_payload = deepcopy(payload)
    update_payload["materials"] = []

    response = client.put(
        "/api/cultivation-logs/"
        "test-update-business-rule-001",
        json=update_payload,
    )

    assert response.status_code == 400

    response_data = response.json()

    assert response_data["detail"]["code"] == (
        "BUSINESS_VALIDATION_FAILED"
    )

    # Database phải giữ nguyên record trước update.
    detail_response = client.get(
        "/api/cultivation-logs/"
        "test-update-business-rule-001"
    )

    assert detail_response.status_code == 200

    stored_log = detail_response.json()["data"]

    assert len(stored_log["materials"]) == 1
    assert (
        stored_log["materials"][0]["material_code"]
        == "NPK"
    )
    assert stored_log["materials"][0]["quantity"] == 20