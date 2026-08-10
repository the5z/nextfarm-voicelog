from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import (
    Draft202012Validator,
    FormatChecker,
)
from jsonschema.exceptions import SchemaError


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIRECTORY = REPOSITORY_ROOT / "contracts"
EXAMPLES_DIRECTORY = CONTRACTS_DIRECTORY / "examples"


SCHEMA_CASES: tuple[tuple[str, Path], ...] = (
    (
        "ai-extraction-response",
        CONTRACTS_DIRECTORY
        / "ai-extraction-response.schema.json",
    ),
    (
        "cultivation-log",
        CONTRACTS_DIRECTORY
        / "cultivation-log.schema.json",
    ),
    (
        "nextfarm-payload",
        CONTRACTS_DIRECTORY
        / "nextfarm-payload.schema.json",
    ),
    (
        "sync-request",
        CONTRACTS_DIRECTORY
        / "sync-request.schema.json",
    ),
    (
        "sync-response",
        CONTRACTS_DIRECTORY
        / "sync-response.schema.json",
    ),
)


EXAMPLE_CASES: tuple[
    tuple[str, Path, Path],
    ...,
] = (
    (
        "ai-response-valid",
        CONTRACTS_DIRECTORY
        / "ai-extraction-response.schema.json",
        EXAMPLES_DIRECTORY
        / "ai-extraction-response.json",
    ),
    (
        "ai-response-missing-fields",
        CONTRACTS_DIRECTORY
        / "ai-extraction-response.schema.json",
        EXAMPLES_DIRECTORY
        / "ai-extraction-missing-fields.json",
    ),
    (
        "cultivation-log-valid",
        CONTRACTS_DIRECTORY
        / "cultivation-log.schema.json",
        EXAMPLES_DIRECTORY
        / "cultivation-log-valid.json",
    ),
    (
        "nextfarm-payload-valid",
        CONTRACTS_DIRECTORY
        / "nextfarm-payload.schema.json",
        EXAMPLES_DIRECTORY
        / "nextfarm-payload.json",
    ),
    (
        "nextfarm-legacy-example-valid",
        CONTRACTS_DIRECTORY
        / "nextfarm-payload.schema.json",
        CONTRACTS_DIRECTORY
        / "nextfarm-production-diary.example.json",
    ),
    (
        "sync-request-valid",
        CONTRACTS_DIRECTORY
        / "sync-request.schema.json",
        CONTRACTS_DIRECTORY
        / "sync-request.example.json",
    ),
    (
        "sync-response-valid",
        CONTRACTS_DIRECTORY
        / "sync-response.schema.json",
        CONTRACTS_DIRECTORY
        / "sync-response.example.json",
    ),
)


def load_json(file_path: Path) -> Any:
    """
    Đọc một file JSON bằng UTF-8.
    """

    assert file_path.exists(), (
        f"Không tìm thấy file: {file_path}"
    )

    try:
        with file_path.open(
            mode="r",
            encoding="utf-8",
        ) as json_file:
            return json.load(json_file)

    except json.JSONDecodeError as error:
        pytest.fail(
            (
                f"File JSON không hợp lệ: "
                f"{relative_path(file_path)}\n"
                f"Dòng {error.lineno}, "
                f"cột {error.colno}: "
                f"{error.msg}"
            )
        )


def relative_path(file_path: Path) -> str:
    """
    Trả về đường dẫn tương đối so với repository.
    """

    return str(
        file_path.relative_to(REPOSITORY_ROOT)
    )


def format_json_path(
    path_parts: list[Any],
) -> str:
    """
    Chuyển đường dẫn lỗi thành dạng dễ đọc.

    Ví dụ:
        $.records[0].materials[0].quantity
    """

    result = "$"

    for path_part in path_parts:
        if isinstance(path_part, int):
            result += f"[{path_part}]"
        else:
            result += f".{path_part}"

    return result


@pytest.mark.parametrize(
    (
        "schema_name",
        "schema_path",
    ),
    SCHEMA_CASES,
    ids=[
        case_name
        for case_name, _ in SCHEMA_CASES
    ],
)
def test_contract_schema_is_valid(
    schema_name: str,
    schema_path: Path,
) -> None:
    """
    Mỗi schema phải hợp lệ theo JSON Schema Draft 2020-12.
    """

    schema_data = load_json(schema_path)

    try:
        Draft202012Validator.check_schema(
            schema_data
        )

    except SchemaError as error:
        pytest.fail(
            (
                f"Schema {schema_name} không hợp lệ.\n"
                f"File: {relative_path(schema_path)}\n"
                f"Lỗi: {error.message}"
            )
        )


@pytest.mark.parametrize(
    (
        "case_name",
        "schema_path",
        "example_path",
    ),
    EXAMPLE_CASES,
    ids=[
        case_name
        for case_name, _, _ in EXAMPLE_CASES
    ],
)
def test_contract_example_matches_schema(
    case_name: str,
    schema_path: Path,
    example_path: Path,
) -> None:
    """
    Mỗi file ví dụ phải tuân thủ schema tương ứng.
    """

    schema_data = load_json(schema_path)
    example_data = load_json(example_path)

    validator = Draft202012Validator(
        schema=schema_data,
        format_checker=FormatChecker(),
    )

    validation_errors = sorted(
        validator.iter_errors(example_data),
        key=lambda error: (
            format_json_path(
                list(error.absolute_path)
            ),
            error.message,
        ),
    )

    if not validation_errors:
        return

    formatted_errors: list[str] = []

    for error in validation_errors:
        json_path = format_json_path(
            list(error.absolute_path)
        )

        formatted_errors.append(
            f"- {json_path}: {error.message}"
        )

    pytest.fail(
        (
            f"Contract example không hợp lệ: "
            f"{case_name}\n"
            f"Schema: {relative_path(schema_path)}\n"
            f"Example: {relative_path(example_path)}\n"
            + "\n".join(formatted_errors)
        )
    )