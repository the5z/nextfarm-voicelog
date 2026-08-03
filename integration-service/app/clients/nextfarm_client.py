from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Mapping, cast
from uuid import uuid4

import httpx


NextFarmMode = Literal["mock", "live"]


class NextFarmClientError(RuntimeError):
    """
    Lỗi chung khi giao tiếp với NextFarm.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


class NextFarmConfigurationError(
    NextFarmClientError
):
    """
    Lỗi cấu hình NextFarm không hợp lệ.
    """


class NextFarmRequestError(
    NextFarmClientError
):
    """
    Lỗi xảy ra trong quá trình gửi request tới NextFarm.
    """


def get_optional_environment_value(
    variable_name: str,
) -> str | None:
    """
    Đọc biến môi trường.

    Chuỗi rỗng hoặc chỉ có khoảng trắng được chuyển thành None.
    """

    value = os.getenv(variable_name)

    if value is None:
        return None

    normalized_value = value.strip()

    return normalized_value or None


@dataclass(frozen=True)
class NextFarmClientConfig:
    """
    Cấu hình kết nối NextFarm.

    mode:
        mock -> không gọi API thật.
        live -> gửi request HTTP tới NextFarm.

    base_url:
        Địa chỉ máy chủ NextFarm.

    api_token:
        Token xác thực khi chạy chế độ live.

    production_diary_path:
        Đường dẫn API tạo nhật ký sản xuất.

    timeout_seconds:
        Thời gian tối đa chờ phản hồi.
    """

    mode: NextFarmMode = "mock"
    base_url: str | None = None
    api_token: str | None = None

    production_diary_path: str = (
        "/api/diary/production"
    )

    timeout_seconds: float = 10.0

    @classmethod
    def from_env(
        cls,
    ) -> "NextFarmClientConfig":
        """
        Tạo cấu hình client từ biến môi trường.
        """

        raw_mode = (
            os.getenv(
                "NEXTFARM_MODE",
                "mock",
            )
            .strip()
            .lower()
        )

        if raw_mode not in {
            "mock",
            "live",
        }:
            raise NextFarmConfigurationError(
                "NEXTFARM_MODE chỉ được là mock hoặc live"
            )

        mode = cast(
            NextFarmMode,
            raw_mode,
        )

        timeout_text = os.getenv(
            "NEXTFARM_TIMEOUT_SECONDS",
            "10",
        ).strip()

        try:
            timeout_seconds = float(
                timeout_text
            )
        except ValueError as error:
            raise NextFarmConfigurationError(
                "NEXTFARM_TIMEOUT_SECONDS phải là một số"
            ) from error

        production_diary_path = os.getenv(
            "NEXTFARM_PRODUCTION_DIARY_PATH",
            "/api/diary/production",
        ).strip()

        if not production_diary_path:
            production_diary_path = (
                "/api/diary/production"
            )

        if not production_diary_path.startswith("/"):
            production_diary_path = (
                f"/{production_diary_path}"
            )

        config = cls(
            mode=mode,
            base_url=get_optional_environment_value(
                "NEXTFARM_BASE_URL"
            ),
            api_token=get_optional_environment_value(
                "NEXTFARM_API_TOKEN"
            ),
            production_diary_path=(
                production_diary_path
            ),
            timeout_seconds=timeout_seconds,
        )

        config.validate()

        return config

    def validate(self) -> None:
        """
        Kiểm tra cấu hình trước khi tạo client.
        """

        if self.mode not in {
            "mock",
            "live",
        }:
            raise NextFarmConfigurationError(
                "Chế độ NextFarm không hợp lệ"
            )

        if self.timeout_seconds <= 0:
            raise NextFarmConfigurationError(
                "Timeout phải lớn hơn 0"
            )

        if not self.production_diary_path:
            raise NextFarmConfigurationError(
                "Thiếu đường dẫn API nhật ký sản xuất"
            )

        if not self.production_diary_path.startswith("/"):
            raise NextFarmConfigurationError(
                "Đường dẫn API phải bắt đầu bằng dấu /"
            )

        if self.mode == "live":
            if not self.base_url:
                raise NextFarmConfigurationError(
                    "Thiếu NEXTFARM_BASE_URL "
                    "khi chạy chế độ live"
                )

            if not self.api_token:
                raise NextFarmConfigurationError(
                    "Thiếu NEXTFARM_API_TOKEN "
                    "khi chạy chế độ live"
                )


class NextFarmClient:
    """
    Client gửi nhật ký sản xuất sang NextFarm.

    Chế độ mock:
        Không tạo kết nối HTTP.

    Chế độ live:
        Gửi JSON tới API NextFarm được cấu hình.
    """

    def __init__(
        self,
        config: NextFarmClientConfig | None = None,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else NextFarmClientConfig.from_env()
        )

        self.config.validate()

        self._http_client = http_client
        self._owns_http_client = False

        if (
            self.config.mode == "live"
            and self._http_client is None
        ):
            base_url = self.config.base_url

            if base_url is None:
                raise NextFarmConfigurationError(
                    "Thiếu địa chỉ NextFarm"
                )

            self._http_client = httpx.Client(
                base_url=base_url.rstrip("/"),
                timeout=self.config.timeout_seconds,
            )

            self._owns_http_client = True

    def __enter__(
        self,
    ) -> "NextFarmClient":
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        self.close()

    def close(self) -> None:
        """
        Đóng HTTP client nếu lớp này tự tạo client.
        """

        if (
            self._owns_http_client
            and self._http_client is not None
        ):
            self._http_client.close()

            self._http_client = None
            self._owns_http_client = False

    def _build_request_headers(
        self,
    ) -> dict[str, str]:
        """
        Tạo header dùng cho mỗi request NextFarm.

        Header được truyền trực tiếp khi gửi request để hoạt động
        cả khi http_client được inject từ bên ngoài trong test.
        """

        api_token = self.config.api_token

        if not api_token:
            raise NextFarmConfigurationError(
                "Thiếu token NextFarm"
            )

        return {
            "Accept": "application/json",
            "Authorization": (
                f"Bearer {api_token}"
            ),
            "X-Integration-Source": (
                "nextfarm-voicelog"
            ),
        }

    def submit_production_diary(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        Gửi một nhật ký sản xuất sang NextFarm.

        payload phải là JSON đã được xử lý bởi
        map_cultivation_log_to_nextfarm().
        """

        if not isinstance(payload, Mapping):
            raise TypeError(
                "payload phải là một mapping"
            )

        normalized_payload = dict(payload)

        if self.config.mode == "mock":
            return self._submit_mock(
                normalized_payload
            )

        return self._submit_live(
            normalized_payload
        )

    def _submit_mock(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Mô phỏng NextFarm tiếp nhận nhật ký thành công.
        """

        metadata = payload.get("metadata")

        client_record_id: str | None = None

        if isinstance(metadata, Mapping):
            raw_client_record_id = metadata.get(
                "client_record_id"
            )

            if raw_client_record_id is not None:
                client_record_id = str(
                    raw_client_record_id
                ).strip()

        external_id = (
            f"mock-{client_record_id}"
            if client_record_id
            else f"mock-{uuid4()}"
        )

        return {
            "success": True,
            "mode": "mock",
            "status": "accepted",
            "status_code": 200,
            "data": {
                "id": external_id,
                "message": (
                    "NextFarm mock đã tiếp nhận nhật ký"
                ),
                "received_payload": payload,
            },
        }

    def _submit_live(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Gửi request HTTP tới NextFarm thật.
        """

        if self._http_client is None:
            raise NextFarmConfigurationError(
                "HTTP client chưa được khởi tạo"
            )

        request_headers = (
            self._build_request_headers()
        )

        try:
            response = self._http_client.post(
                self.config.production_diary_path,
                json=payload,
                headers=request_headers,
            )

        except httpx.TimeoutException as error:
            raise NextFarmRequestError(
                "Hết thời gian chờ phản hồi từ NextFarm"
            ) from error

        except httpx.RequestError as error:
            raise NextFarmRequestError(
                "Không thể kết nối đến NextFarm"
            ) from error

        if not response.is_success:
            response_text = response.text.strip()

            if len(response_text) > 1000:
                response_text = (
                    f"{response_text[:1000]}..."
                )

            if not response_text:
                response_text = (
                    "NextFarm không trả về nội dung lỗi"
                )

            raise NextFarmRequestError(
                (
                    "NextFarm trả về HTTP "
                    f"{response.status_code}: "
                    f"{response_text}"
                ),
                status_code=response.status_code,
            )

        try:
            response_data = response.json()
        except ValueError as error:
            raise NextFarmRequestError(
                "NextFarm trả về dữ liệu không phải JSON",
                status_code=response.status_code,
            ) from error

        if not isinstance(response_data, dict):
            raise NextFarmRequestError(
                "JSON phản hồi từ NextFarm phải là object",
                status_code=response.status_code,
            )

        return {
            "success": True,
            "mode": "live",
            "status": "accepted",
            "status_code": response.status_code,
            "data": response_data,
        }