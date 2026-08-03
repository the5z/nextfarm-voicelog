from typing import Any

import httpx
import pytest

from app.clients.nextfarm_client import (
    NextFarmClient,
    NextFarmClientConfig,
    NextFarmConfigurationError,
    NextFarmRequestError,
)


def build_nextfarm_payload() -> dict[str, Any]:
    """
    Tạo JSON NextFarm mô phỏng dùng trong test.
    """

    return {
        "name": "Bón phân",
        "start": "2026-08-03T08:00:00+07:00",
        "end": "2026-08-03T08:00:00+07:00",
        "description": "Bón 20 kg NPK",
        "images": [],
        "location": "LO_A1",
        "assigned_to": "NV001",
        "category_task_id": "BON_PHAN",
        "season_id": "LO_A1",
        "metadata": {
            "schema_version": "1.0",
            "client_record_id": "client-test-001",
            "source": "voice",
            "integration_source": (
                "nextfarm-voicelog"
            ),
        },
    }


def test_config_defaults_to_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Khi không cấu hình, client phải dùng chế độ mock.
    """

    monkeypatch.delenv(
        "NEXTFARM_MODE",
        raising=False,
    )

    monkeypatch.delenv(
        "NEXTFARM_BASE_URL",
        raising=False,
    )

    monkeypatch.delenv(
        "NEXTFARM_API_TOKEN",
        raising=False,
    )

    config = NextFarmClientConfig.from_env()

    assert config.mode == "mock"
    assert config.timeout_seconds == 10
    assert config.production_diary_path == (
        "/api/diary/production"
    )


def test_mock_submit_production_diary() -> None:
    """
    Chế độ mock phải trả về kết quả thành công
    mà không gọi HTTP.
    """

    config = NextFarmClientConfig(
        mode="mock",
    )

    client = NextFarmClient(
        config=config,
    )

    result = client.submit_production_diary(
        build_nextfarm_payload()
    )

    assert result["success"] is True
    assert result["mode"] == "mock"
    assert result["status"] == "accepted"
    assert result["status_code"] == 200

    assert result["data"]["id"] == (
        "mock-client-test-001"
    )

    assert (
        result["data"]["received_payload"]["name"]
        == "Bón phân"
    )


def test_live_mode_requires_configuration() -> None:
    """
    Chế độ live phải có URL và token.
    """

    config = NextFarmClientConfig(
        mode="live",
        base_url=None,
        api_token=None,
    )

    with pytest.raises(
        NextFarmConfigurationError,
        match="NEXTFARM_BASE_URL",
    ):
        NextFarmClient(
            config=config,
        )


def test_live_submit_success() -> None:
    """
    Chế độ live phải gửi JSON và Bearer token đúng.
    """

    captured_request: httpx.Request | None = None

    def request_handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal captured_request

        captured_request = request

        return httpx.Response(
            status_code=201,
            json={
                "id": 987,
                "status": "created",
            },
            request=request,
        )

    transport = httpx.MockTransport(
        request_handler
    )

    with httpx.Client(
        base_url="https://nextfarm.example.test",
        transport=transport,
    ) as http_client:
        config = NextFarmClientConfig(
            mode="live",
            base_url=(
                "https://nextfarm.example.test"
            ),
            api_token="test-token",
            production_diary_path=(
                "/api/diary/production"
            ),
        )

        client = NextFarmClient(
            config=config,
            http_client=http_client,
        )

        result = client.submit_production_diary(
            build_nextfarm_payload()
        )

    assert result["success"] is True
    assert result["mode"] == "live"
    assert result["status_code"] == 201
    assert result["data"]["id"] == 987

    assert captured_request is not None

    assert captured_request.url.path == (
        "/api/diary/production"
    )

    assert captured_request.headers[
        "authorization"
    ] == "Bearer test-token"


def test_live_submit_handles_http_error() -> None:
    """
    HTTP 400 hoặc 500 từ NextFarm phải được báo lỗi.
    """

    def request_handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=400,
            json={
                "message": "Invalid payload",
            },
            request=request,
        )

    transport = httpx.MockTransport(
        request_handler
    )

    with httpx.Client(
        base_url="https://nextfarm.example.test",
        transport=transport,
    ) as http_client:
        config = NextFarmClientConfig(
            mode="live",
            base_url=(
                "https://nextfarm.example.test"
            ),
            api_token="test-token",
        )

        client = NextFarmClient(
            config=config,
            http_client=http_client,
        )

        with pytest.raises(
            NextFarmRequestError,
            match="HTTP 400",
        ) as exception_info:
            client.submit_production_diary(
                build_nextfarm_payload()
            )

    assert (
        exception_info.value.status_code
        == 400
    )


def test_live_submit_rejects_invalid_json() -> None:
    """
    Phản hồi thành công nhưng không phải JSON phải bị từ chối.
    """

    def request_handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            text="not-json",
            request=request,
        )

    transport = httpx.MockTransport(
        request_handler
    )

    with httpx.Client(
        base_url="https://nextfarm.example.test",
        transport=transport,
    ) as http_client:
        config = NextFarmClientConfig(
            mode="live",
            base_url=(
                "https://nextfarm.example.test"
            ),
            api_token="test-token",
        )

        client = NextFarmClient(
            config=config,
            http_client=http_client,
        )

        with pytest.raises(
            NextFarmRequestError,
            match="không phải JSON",
        ):
            client.submit_production_diary(
                build_nextfarm_payload()
            )


def test_live_submit_handles_timeout() -> None:
    """
    Timeout phải được chuyển thành NextFarmRequestError.
    """

    def request_handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "Request timeout",
            request=request,
        )

    transport = httpx.MockTransport(
        request_handler
    )

    with httpx.Client(
        base_url="https://nextfarm.example.test",
        transport=transport,
    ) as http_client:
        config = NextFarmClientConfig(
            mode="live",
            base_url=(
                "https://nextfarm.example.test"
            ),
            api_token="test-token",
        )

        client = NextFarmClient(
            config=config,
            http_client=http_client,
        )

        with pytest.raises(
            NextFarmRequestError,
            match="Hết thời gian",
        ):
            client.submit_production_diary(
                build_nextfarm_payload()
            )