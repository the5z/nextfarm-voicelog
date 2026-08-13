import json
import re
import unicodedata
from collections import defaultdict
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

    # Tách số và chữ: 20kg -> 20 kg
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


def percent(correct: int, total: int):
    if total == 0:
        return None

    return round(
        correct / total * 100,
        2,
    )


def empty_group_stats() -> dict:
    return {
        "total_cases": 0,
        "successful_cases": 0,
        "material_cases": 0,
        "word_errors": 0,
        "reference_words": 0,
        "processing_time_ms": 0.0,
        "activity_correct": 0,
        "lot_correct": 0,
        "material_correct": 0,
        "quantity_correct": 0,
        "unit_correct": 0,
        "time_correct": 0,
        "full_record_correct": 0,
    }


def update_group_stats(
    stats: dict,
    case_data: dict,
) -> None:
    stats["total_cases"] += 1

    if not case_data["success"]:
        return

    stats["successful_cases"] += 1

    stats["word_errors"] += (
        case_data["word_errors"]
    )

    stats["reference_words"] += (
        case_data["reference_words"]
    )

    stats["processing_time_ms"] += (
        case_data["processing_time_ms"]
    )

    if case_data["activity_correct"]:
        stats["activity_correct"] += 1

    if case_data["lot_correct"]:
        stats["lot_correct"] += 1

    if case_data["time_correct"]:
        stats["time_correct"] += 1

    if case_data["full_record_correct"]:
        stats["full_record_correct"] += 1

    if case_data["has_material"]:
        stats["material_cases"] += 1

        if case_data["material_correct"]:
            stats["material_correct"] += 1

        if case_data["quantity_correct"]:
            stats["quantity_correct"] += 1

        if case_data["unit_correct"]:
            stats["unit_correct"] += 1


def finalize_group_stats(
    stats: dict,
) -> dict:
    if stats["reference_words"]:
        wer_percent = round(
            stats["word_errors"]
            / stats["reference_words"]
            * 100,
            2,
        )
    else:
        wer_percent = None

    if stats["successful_cases"]:
        average_processing_time_ms = round(
            stats["processing_time_ms"]
            / stats["successful_cases"],
            2,
        )
    else:
        average_processing_time_ms = None

    return {
        "summary": {
            "total_cases": stats["total_cases"],
            "successful_cases": (
                stats["successful_cases"]
            ),
            "failed_cases": (
                stats["total_cases"]
                - stats["successful_cases"]
            ),
            "material_cases": (
                stats["material_cases"]
            ),
        },
        "metrics": {
            "wer_percent": wer_percent,
            "activity_accuracy_percent": percent(
                stats["activity_correct"],
                stats["total_cases"],
            ),
            "lot_accuracy_percent": percent(
                stats["lot_correct"],
                stats["total_cases"],
            ),
            "material_accuracy_percent": percent(
                stats["material_correct"],
                stats["material_cases"],
            ),
            "quantity_accuracy_percent": percent(
                stats["quantity_correct"],
                stats["material_cases"],
            ),
            "unit_accuracy_percent": percent(
                stats["unit_correct"],
                stats["material_cases"],
            ),
            "time_accuracy_percent": percent(
                stats["time_correct"],
                stats["total_cases"],
            ),
            "full_record_accuracy_percent": percent(
                stats["full_record_correct"],
                stats["total_cases"],
            ),
            "average_processing_time_ms": (
                average_processing_time_ms
            ),
        },
    }


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


def format_percent(value) -> str:
    if value is None:
        return "N/A"

    return f"{value}%"


def format_ms(value) -> str:
    if value is None:
        return "N/A"

    return f"{value} ms"


def main() -> None:
    ground_truth_rows = load_jsonl(
        GROUND_TRUTH_FILE
    )

    prediction_rows = load_jsonl(
        PREDICTIONS_FILE
    )

    predictions = {
        row["test_case_id"]: row
        for row in prediction_rows
    }

    overall_stats = empty_group_stats()

    speaker_type_stats = defaultdict(
        empty_group_stats
    )

    accent_stats = defaultdict(
        empty_group_stats
    )

    case_results = []

    print("=" * 72)
    print(
        "NEXTFARM VOICELOG - BENCHMARK EVALUATION"
    )
    print("=" * 72)

    for expected in ground_truth_rows:
        test_case_id = expected["test_case_id"]

        result = predictions.get(test_case_id)

        accent = expected.get(
            "accent",
            "unknown",
        )

        speaker_type = expected.get(
            "speaker_type",
            "human_unspecified",
        )

        print(f"\n[{test_case_id}]")

        if (
            not result
            or not result.get("success")
        ):
            print("Prediction: FAILED")

            case_data = {
                "test_case_id": test_case_id,
                "success": False,
                "accent": accent,
                "speaker_type": speaker_type,
            }

            case_results.append(case_data)

            update_group_stats(
                overall_stats,
                case_data,
            )

            update_group_stats(
                speaker_type_stats[
                    speaker_type
                ],
                case_data,
            )

            update_group_stats(
                accent_stats[accent],
                case_data,
            )

            continue

        prediction = result["prediction"]

        structured = prediction[
            "structured_data"
        ]

        transcript = prediction[
            "transcript"
        ]

        word_errors, reference_words = (
            calculate_wer(
                expected[
                    "ground_truth_transcript"
                ],
                transcript,
            )
        )

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

        has_material = bool(
            materials_expected
        )

        full_record_correct = (
            activity_correct
            and lot_correct
            and time_correct
            and material_result[
                "all_correct"
            ]
        )

        total_time_ms = (
            result
            .get("timing", {})
            .get("total_time_ms", 0)
        )

        case_wer = (
            word_errors
            / reference_words
            * 100
            if reference_words
            else 0
        )

        case_data = {
            "test_case_id": test_case_id,
            "success": True,
            "accent": accent,
            "speaker_type": speaker_type,
            "wer_percent": round(
                case_wer,
                2,
            ),
            "word_errors": word_errors,
            "reference_words": (
                reference_words
            ),
            "activity_correct": (
                activity_correct
            ),
            "lot_correct": lot_correct,
            "has_material": has_material,
            "material_correct": (
                material_result[
                    "material_correct"
                ]
                if has_material
                else None
            ),
            "quantity_correct": (
                material_result[
                    "quantity_correct"
                ]
                if has_material
                else None
            ),
            "unit_correct": (
                material_result[
                    "unit_correct"
                ]
                if has_material
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

        case_results.append(case_data)

        update_group_stats(
            overall_stats,
            case_data,
        )

        update_group_stats(
            speaker_type_stats[
                speaker_type
            ],
            case_data,
        )

        update_group_stats(
            accent_stats[accent],
            case_data,
        )

        print(
            f"Accent: {accent}"
        )

        print(
            f"Speaker type: {speaker_type}"
        )

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

        if has_material:
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

    overall_metrics = finalize_group_stats(
        overall_stats
    )

    by_speaker_type = {
        key: finalize_group_stats(value)
        for key, value
        in speaker_type_stats.items()
    }

    by_accent = {
        key: finalize_group_stats(value)
        for key, value
        in accent_stats.items()
    }

    metrics = {
        "overall": overall_metrics,
        "by_speaker_type": by_speaker_type,
        "by_accent": by_accent,
        "cases": case_results,
    }

    save_metrics(metrics)

    print("\n" + "=" * 72)
    print("OVERALL METRICS")
    print("=" * 72)

    overall = overall_metrics[
        "metrics"
    ]

    summary = overall_metrics[
        "summary"
    ]

    print(
        f"Total cases: "
        f"{summary['total_cases']}"
    )

    print(
        f"Successful cases: "
        f"{summary['successful_cases']}/"
        f"{summary['total_cases']}"
    )

    print(
        "WER:",
        format_percent(
            overall["wer_percent"]
        ),
    )

    print(
        "Activity Accuracy:",
        format_percent(
            overall[
                "activity_accuracy_percent"
            ]
        ),
    )

    print(
        "Lot Accuracy:",
        format_percent(
            overall[
                "lot_accuracy_percent"
            ]
        ),
    )

    print(
        "Material Accuracy:",
        format_percent(
            overall[
                "material_accuracy_percent"
            ]
        ),
    )

    print(
        "Quantity Accuracy:",
        format_percent(
            overall[
                "quantity_accuracy_percent"
            ]
        ),
    )

    print(
        "Unit Accuracy:",
        format_percent(
            overall[
                "unit_accuracy_percent"
            ]
        ),
    )

    print(
        "Time Accuracy:",
        format_percent(
            overall[
                "time_accuracy_percent"
            ]
        ),
    )

    print(
        "Full Record Accuracy:",
        format_percent(
            overall[
                "full_record_accuracy_percent"
            ]
        ),
    )

    print(
        "Average Processing Time:",
        format_ms(
            overall[
                "average_processing_time_ms"
            ]
        ),
    )

    print("\n" + "=" * 72)
    print("BY SPEAKER TYPE")
    print("=" * 72)

    for speaker_type, data in (
        by_speaker_type.items()
    ):
        group_metrics = data["metrics"]
        group_summary = data["summary"]

        print(
            f"\n[{speaker_type}]"
        )

        print(
            f"Cases: "
            f"{group_summary['total_cases']}"
        )

        print(
            "WER:",
            format_percent(
                group_metrics[
                    "wer_percent"
                ]
            ),
        )

        print(
            "Activity Accuracy:",
            format_percent(
                group_metrics[
                    "activity_accuracy_percent"
                ]
            ),
        )

        print(
            "Lot Accuracy:",
            format_percent(
                group_metrics[
                    "lot_accuracy_percent"
                ]
            ),
        )

        print(
            "Material Accuracy:",
            format_percent(
                group_metrics[
                    "material_accuracy_percent"
                ]
            ),
        )

        print(
            "Quantity Accuracy:",
            format_percent(
                group_metrics[
                    "quantity_accuracy_percent"
                ]
            ),
        )

        print(
            "Unit Accuracy:",
            format_percent(
                group_metrics[
                    "unit_accuracy_percent"
                ]
            ),
        )

        print(
            "Time Accuracy:",
            format_percent(
                group_metrics[
                    "time_accuracy_percent"
                ]
            ),
        )

        print(
            "Full Record Accuracy:",
            format_percent(
                group_metrics[
                    "full_record_accuracy_percent"
                ]
            ),
        )

    print("\n" + "=" * 72)
    print("BY ACCENT")
    print("=" * 72)

    for accent, data in by_accent.items():
        group_metrics = data["metrics"]
        group_summary = data["summary"]

        print(
            f"\n[{accent}]"
        )

        print(
            f"Cases: "
            f"{group_summary['total_cases']}"
        )

        print(
            "WER:",
            format_percent(
                group_metrics[
                    "wer_percent"
                ]
            ),
        )

        print(
            "Activity Accuracy:",
            format_percent(
                group_metrics[
                    "activity_accuracy_percent"
                ]
            ),
        )

        print(
            "Lot Accuracy:",
            format_percent(
                group_metrics[
                    "lot_accuracy_percent"
                ]
            ),
        )

        print(
            "Material Accuracy:",
            format_percent(
                group_metrics[
                    "material_accuracy_percent"
                ]
            ),
        )

        print(
            "Quantity Accuracy:",
            format_percent(
                group_metrics[
                    "quantity_accuracy_percent"
                ]
            ),
        )

        print(
            "Unit Accuracy:",
            format_percent(
                group_metrics[
                    "unit_accuracy_percent"
                ]
            ),
        )

        print(
            "Time Accuracy:",
            format_percent(
                group_metrics[
                    "time_accuracy_percent"
                ]
            ),
        )

        print(
            "Full Record Accuracy:",
            format_percent(
                group_metrics[
                    "full_record_accuracy_percent"
                ]
            ),
        )

    print(
        f"\nMetrics file: {METRICS_FILE}"
    )


if __name__ == "__main__":
    main()