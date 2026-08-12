import json
import re
import unicodedata
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

GROUND_TRUTH_FILE = (
    BASE_DIR
    / "ground_truth"
    / "dataset.jsonl"
)

PREDICTIONS_FILE = (
    BASE_DIR
    / "results"
    / "predictions.jsonl"
)

METRICS_FILE = (
    BASE_DIR
    / "results"
    / "metrics.json"
)


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def normalize_text(value) -> str:
    if value is None:
        return ""

    text = str(value)

    text = unicodedata.normalize(
        "NFC",
        text,
    )

    text = text.lower().strip()

    # Tách số và chữ:
    # 20kg -> 20 kg
    text = re.sub(
        r"(?<=\d)(?=[a-zA-ZÀ-ỹ])",
        " ",
        text,
    )

    text = re.sub(
        r"(?<=[a-zA-ZÀ-ỹ])(?=\d)",
        " ",
        text,
    )

    # Dấu câu / ký tự đặc biệt -> khoảng trắng
    text = re.sub(
        r"[^\wÀ-ỹ]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def word_error_count(
    reference_words: list[str],
    hypothesis_words: list[str],
) -> int:
    rows = len(reference_words) + 1
    cols = len(hypothesis_words) + 1

    dp = [
        [0] * cols
        for _ in range(rows)
    ]

    for i in range(rows):
        dp[i][0] = i

    for j in range(cols):
        dp[0][j] = j

    for i in range(1, rows):
        for j in range(1, cols):
            if (
                reference_words[i - 1]
                == hypothesis_words[j - 1]
            ):
                cost = 0
            else:
                cost = 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[-1][-1]


def calculate_wer(
    reference: str,
    hypothesis: str,
) -> tuple[int, int]:
    reference_words = normalize_text(
        reference
    ).split()

    hypothesis_words = normalize_text(
        hypothesis
    ).split()

    errors = word_error_count(
        reference_words,
        hypothesis_words,
    )

    return errors, len(reference_words)


def values_match(expected, predicted) -> bool:
    if expected is None and predicted is None:
        return True

    if isinstance(expected, (int, float)):
        try:
            return float(expected) == float(predicted)
        except (TypeError, ValueError):
            return False

    return (
        normalize_text(expected)
        == normalize_text(predicted)
    )


def compare_materials(
    expected: list[dict],
    predicted: list[dict],
) -> dict:
    if not expected and not predicted:
        return {
            "material_correct": True,
            "quantity_correct": True,
            "unit_correct": True,
            "all_correct": True,
        }

    if len(expected) != len(predicted):
        return {
            "material_correct": False,
            "quantity_correct": False,
            "unit_correct": False,
            "all_correct": False,
        }

    material_correct = True
    quantity_correct = True
    unit_correct = True

    for expected_item, predicted_item in zip(
        expected,
        predicted,
    ):
        if not values_match(
            expected_item.get("material_text"),
            predicted_item.get("material_text"),
        ):
            material_correct = False

        if not values_match(
            expected_item.get("quantity"),
            predicted_item.get("quantity"),
        ):
            quantity_correct = False

        if not values_match(
            expected_item.get("unit_text"),
            predicted_item.get("unit_text"),
        ):
            unit_correct = False

    return {
        "material_correct": material_correct,
        "quantity_correct": quantity_correct,
        "unit_correct": unit_correct,
        "all_correct": (
            material_correct
            and quantity_correct
            and unit_correct
        ),
    }


def percent(correct: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(
        correct / total * 100,
        2,
    )


def save_metrics(metrics: dict) -> None:
    METRICS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with METRICS_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    ground_truth_rows = load_jsonl(
        GROUND_TRUTH_FILE
    )

    prediction_rows = load_jsonl(
        PREDICTIONS_FILE
    )

    ground_truth = {
        row["test_case_id"]: row
        for row in ground_truth_rows
    }

    predictions = {
        row["test_case_id"]: row
        for row in prediction_rows
    }

    total_cases = len(ground_truth)

    counters = {
        "activity": 0,
        "lot": 0,
        "material": 0,
        "quantity": 0,
        "unit": 0,
        "time": 0,
        "full_record": 0,
    }

    material_case_count = 0

    total_word_errors = 0
    total_reference_words = 0

    total_processing_time_ms = 0
    successful_cases = 0

    case_results = []

    print("=" * 72)
    print("NEXTFARM VOICELOG - BENCHMARK EVALUATION")
    print("=" * 72)

    for test_case_id, expected in ground_truth.items():
        result = predictions.get(test_case_id)

        print(f"\n[{test_case_id}]")

        if not result or not result.get("success"):
            print("Prediction: FAILED")

            case_results.append(
                {
                    "test_case_id": test_case_id,
                    "success": False,
                }
            )

            continue

        successful_cases += 1

        prediction = result["prediction"]

        structured = prediction[
            "structured_data"
        ]

        transcript = prediction[
            "transcript"
        ]

        errors, reference_words = calculate_wer(
            expected[
                "ground_truth_transcript"
            ],
            transcript,
        )

        total_word_errors += errors
        total_reference_words += reference_words

        activity_correct = values_match(
            expected.get("activity_text"),
            structured.get("activity_text"),
        )

        lot_correct = values_match(
            expected.get("lot_text"),
            structured.get("lot_text"),
        )

        time_correct = values_match(
            expected.get("time_text"),
            structured.get("time_text"),
        )

        materials_expected = expected.get(
            "materials",
            [],
        )

        materials_predicted = structured.get(
            "materials",
            [],
        )

        material_result = compare_materials(
            materials_expected,
            materials_predicted,
        )

        if activity_correct:
            counters["activity"] += 1

        if lot_correct:
            counters["lot"] += 1

        if time_correct:
            counters["time"] += 1

        if materials_expected:
            material_case_count += 1

            if material_result[
                "material_correct"
            ]:
                counters["material"] += 1

            if material_result[
                "quantity_correct"
            ]:
                counters["quantity"] += 1

            if material_result[
                "unit_correct"
            ]:
                counters["unit"] += 1

        full_record_correct = (
            activity_correct
            and lot_correct
            and time_correct
            and material_result[
                "all_correct"
            ]
        )

        if full_record_correct:
            counters["full_record"] += 1

        total_time_ms = (
            result
            .get("timing", {})
            .get("total_time_ms", 0)
        )

        total_processing_time_ms += total_time_ms

        case_wer = (
            errors / reference_words * 100
            if reference_words
            else 0
        )

        case_result = {
            "test_case_id": test_case_id,
            "success": True,
            "wer_percent": round(
                case_wer,
                2,
            ),
            "activity_correct": activity_correct,
            "lot_correct": lot_correct,
            "material_correct": (
                material_result["material_correct"]
                if materials_expected
                else None
            ),
            "quantity_correct": (
                material_result["quantity_correct"]
                if materials_expected
                else None
            ),
            "unit_correct": (
                material_result["unit_correct"]
                if materials_expected
                else None
            ),
            "time_correct": time_correct,
            "full_record_correct": (
                full_record_correct
            ),
            "processing_time_ms": (
                total_time_ms
            ),
        }

        case_results.append(case_result)

        print(
            f"WER: {case_wer:.2f}%"
        )

        print(
            "Activity:",
            "PASS"
            if activity_correct
            else "FAIL",
        )

        print(
            "Lot:",
            "PASS"
            if lot_correct
            else "FAIL",
        )

        if materials_expected:
            print(
                "Material:",
                "PASS"
                if material_result[
                    "material_correct"
                ]
                else "FAIL",
            )

            print(
                "Quantity:",
                "PASS"
                if material_result[
                    "quantity_correct"
                ]
                else "FAIL",
            )

            print(
                "Unit:",
                "PASS"
                if material_result[
                    "unit_correct"
                ]
                else "FAIL",
            )
        else:
            print("Material: N/A")
            print("Quantity: N/A")
            print("Unit: N/A")

        print(
            "Time:",
            "PASS"
            if time_correct
            else "FAIL",
        )

        print(
            "Full record:",
            "PASS"
            if full_record_correct
            else "FAIL",
        )

    overall_wer = (
        total_word_errors
        / total_reference_words
        * 100
        if total_reference_words
        else 0
    )

    average_processing_time_ms = (
        total_processing_time_ms
        / successful_cases
        if successful_cases
        else 0
    )

    metrics = {
        "summary": {
            "total_cases": total_cases,
            "successful_cases": successful_cases,
            "failed_cases": (
                total_cases
                - successful_cases
            ),
            "material_cases": material_case_count,
        },
        "metrics": {
            "wer_percent": round(
                overall_wer,
                2,
            ),
            "activity_accuracy_percent": percent(
                counters["activity"],
                total_cases,
            ),
            "lot_accuracy_percent": percent(
                counters["lot"],
                total_cases,
            ),
            "material_accuracy_percent": percent(
                counters["material"],
                material_case_count,
            ),
            "quantity_accuracy_percent": percent(
                counters["quantity"],
                material_case_count,
            ),
            "unit_accuracy_percent": percent(
                counters["unit"],
                material_case_count,
            ),
            "time_accuracy_percent": percent(
                counters["time"],
                total_cases,
            ),
            "full_record_accuracy_percent": percent(
                counters["full_record"],
                total_cases,
            ),
            "average_processing_time_ms": round(
                average_processing_time_ms,
                2,
            ),
        },
        "cases": case_results,
    }

    save_metrics(metrics)

    print("\n" + "=" * 72)
    print("FINAL METRICS")
    print("=" * 72)

    print(
        f"Total cases: {total_cases}"
    )

    print(
        f"Successful cases: "
        f"{successful_cases}/{total_cases}"
    )

    print(
        f"WER: {overall_wer:.2f}%"
    )

    print(
        "Activity Accuracy:",
        f"{percent(counters['activity'], total_cases)}%",
    )

    print(
        "Lot Accuracy:",
        f"{percent(counters['lot'], total_cases)}%",
    )

    print(
        "Material Accuracy:",
        f"{percent(counters['material'], material_case_count)}%",
    )

    print(
        "Quantity Accuracy:",
        f"{percent(counters['quantity'], material_case_count)}%",
    )

    print(
        "Unit Accuracy:",
        f"{percent(counters['unit'], material_case_count)}%",
    )

    print(
        "Time Accuracy:",
        f"{percent(counters['time'], total_cases)}%",
    )

    print(
        "Full Record Accuracy:",
        f"{percent(counters['full_record'], total_cases)}%",
    )

    print(
        "Average Processing Time:",
        f"{average_processing_time_ms:.2f} ms",
    )

    print(
        f"Metrics file: {METRICS_FILE}"
    )


if __name__ == "__main__":
    main()