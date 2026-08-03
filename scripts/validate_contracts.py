from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
EXAMPLES_DIR = CONTRACTS_DIR / "examples"


@dataclass(frozen=True)
class ContractCase:
    """
    Khai báo một schema và các file ví dụ
    cần được kiểm tra theo schema đó.
    """

    name: str
    schema_path: Path
    example_paths: tuple[Path, ...]


CONTRACT_CASES: tuple[ContractCase, ...] = (
    ContractCase(
        name="Speech/AI extraction response",
        schema_path=(
            CONTRACTS_DIR
            / "ai-extraction-response.schema.json"
        ),
        example_paths=(
            EXAMPLES_DIR
            / "ai-extraction-response.json",
            EXAMPLES_DIR
            / "ai-extraction-missing-fields.json",
        ),
    ),
    ContractCase(
        name="Cultivation log",
        schema_path=(
            CONTRACTS_DIR
            / "cultivation-log.schema.json"
        ),
        example_paths=(
            EXAMPLES_DIR
            / "cultivation-log-valid.json",
        ),
    ),
    ContractCase(
        name="NextFarm mock payload",
        schema_path=(
            CONTRACTS_DIR
            / "nextfarm-payload.schema.json"
        ),
        example_paths=(
            EXAMPLES_DIR
            / "nextfarm-payload.json",
            CONTRACTS_DIR
            / "nextfarm-production-diary.example.json",
        ),
    ),
)


def configure_terminal_encoding() -> None:
    """
    Cấu hình stdout dùng UTF-8 để Windows Terminal
    hiển thị tiếng Việt đúng.
    """

    reconfigure = getattr(
        sys.stdout,
        "reconfigure",
        None,
    )

    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def load_json(file_path: Path) -> Any:
    """
    Đọc một file JSON bằng UTF-8.
    """

    with file_path.open(
        mode="r",
        encoding="utf-8",
    ) as json_file:
        return json.load(json_file)


def format_json_path(
    path_parts: list[Any],
) -> str:
    """
    Chuyển đường dẫn lỗi JSON thành dạng dễ đọc.

    Ví dụ:
        $.materials[0].quantity
    """

    result = "$"

    for part in path_parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"

    return result


def print_validation_errors(
    errors: list[Any],
) -> None:
    """
    In danh sách lỗi validation theo vị trí trong JSON.
    """

    sorted_errors = sorted(
        errors,
        key=lambda error: (
            format_json_path(
                list(error.absolute_path)
            ),
            error.message,
        ),
    )

    for error in sorted_errors:
        json_path = format_json_path(
            list(error.absolute_path)
        )

        print(
            f"      - {json_path}: "
            f"{error.message}"
        )


def validate_contract_case(
    contract_case: ContractCase,
) -> tuple[int, int]:
    """
    Kiểm tra một schema và toàn bộ file ví dụ của schema.

    Giá trị trả về:
        total_examples: tổng số file ví dụ
        failed_examples: số file không hợp lệ
    """

    total_examples = len(
        contract_case.example_paths
    )

    print()
    print(f"Contract: {contract_case.name}")
    print(
        "Schema:   "
        f"{contract_case.schema_path.relative_to(PROJECT_ROOT)}"
    )

    try:
        schema_data = load_json(
            contract_case.schema_path
        )

    except FileNotFoundError:
        print(
            "  [FAIL] Không tìm thấy file schema."
        )
        return total_examples, total_examples

    except json.JSONDecodeError as error:
        print(
            "  [FAIL] Schema không phải JSON hợp lệ:"
        )
        print(
            f"      Dòng {error.lineno}, "
            f"cột {error.colno}: "
            f"{error.msg}"
        )
        return total_examples, total_examples

    try:
        Draft202012Validator.check_schema(
            schema_data
        )

    except SchemaError as error:
        print(
            "  [FAIL] Schema không hợp lệ "
            "theo JSON Schema Draft 2020-12:"
        )
        print(f"      - {error.message}")
        return total_examples, total_examples

    print(
        "  [OK] Schema hợp lệ theo Draft 2020-12."
    )

    validator = Draft202012Validator(
        schema=schema_data,
        format_checker=FormatChecker(),
    )

    failed_examples = 0

    for example_path in contract_case.example_paths:
        relative_path = example_path.relative_to(
            PROJECT_ROOT
        )

        try:
            example_data = load_json(
                example_path
            )

        except FileNotFoundError:
            failed_examples += 1

            print(
                f"  [FAIL] {relative_path}: "
                "không tìm thấy file."
            )
            continue

        except json.JSONDecodeError as error:
            failed_examples += 1

            print(
                f"  [FAIL] {relative_path}: "
                "JSON không hợp lệ."
            )

            print(
                f"      Dòng {error.lineno}, "
                f"cột {error.colno}: "
                f"{error.msg}"
            )
            continue

        errors = list(
            validator.iter_errors(
                example_data
            )
        )

        if errors:
            failed_examples += 1

            print(
                f"  [FAIL] {relative_path}"
            )

            print_validation_errors(errors)

        else:
            print(
                f"  [OK]   {relative_path}"
            )

    return total_examples, failed_examples


def main() -> int:
    """
    Chạy kiểm tra toàn bộ JSON contract.
    """

    configure_terminal_encoding()

    print(
        "Kiểm tra JSON Integration Contracts"
    )

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    total_examples = 0
    failed_examples = 0

    for contract_case in CONTRACT_CASES:
        case_total, case_failed = (
            validate_contract_case(
                contract_case
            )
        )

        total_examples += case_total
        failed_examples += case_failed

    passed_examples = (
        total_examples - failed_examples
    )

    print()
    print("=" * 60)

    print(
        f"Kết quả: "
        f"{passed_examples}/{total_examples} "
        "file ví dụ hợp lệ."
    )

    if failed_examples > 0:
        print(
            f"Có {failed_examples} file "
            "không hợp lệ."
        )
        return 1

    print(
        "Tất cả JSON contract đều hợp lệ."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())