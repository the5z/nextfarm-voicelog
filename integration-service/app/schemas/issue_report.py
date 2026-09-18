from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


IssueType = Literal[
    "Sâu",
    "Bệnh",
    "Thời tiết",
    "Tưới tiêu",
    "Khác",
]

IssueSeverity = Literal[
    "Thấp",
    "Vừa",
    "Cao",
    "Nguy cấp",
]


class IssueReportCreateRequest(BaseModel):
    """
    Structured data đầu vào của
    CREATE_ISSUE_REPORT.

    Integration không đọc transcript
    và không thực hiện AI extraction.
    """

    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    plot_text: str = Field(
        min_length=1,
    )

    issue_type_text: str = Field(
        min_length=1,
    )

    severity_text: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    photo: str | None = None

    note: str | None = None

    confirmed: bool = False

    @field_validator(
        "client_record_id",
        "plot_text",
        "issue_type_text",
        "severity_text",
        "description",
        mode="before",
    )
    @classmethod
    def strip_required_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "photo",
        "note",
        mode="before",
    )
    @classmethod
    def strip_optional_text(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            normalized = value.strip()

            if not normalized:
                return None

            return normalized

        return value


class IssueReportInput(BaseModel):
    """
    Canonical input sau khi Integration
    resolve và validate structured data.
    """

    client_record_id: str = Field(
        min_length=1,
        max_length=100,
    )

    plot_code: str = Field(
        min_length=1,
        max_length=50,
    )

    issue_type: IssueType

    severity: IssueSeverity

    description: str = Field(
        min_length=1,
    )

    photo: str | None = None

    note: str | None = None

    confirmed: bool = False

    @field_validator(
        "plot_code",
        mode="before",
    )
    @classmethod
    def normalize_plot_code(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return (
                value
                .strip()
                .upper()
            )

        return value


class IssueReportSaveResponse(BaseModel):
    success: bool

    status: Literal[
        "saved",
        "already_exists",
        "updated",
    ]

    data: dict[str, Any]


class IssueReportListResponse(BaseModel):
    success: bool

    data: list[
        dict[str, Any]
    ]


class IssueReportGetResponse(BaseModel):
    success: bool

    data: dict[str, Any]