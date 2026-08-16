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

RAW_FILE = (
    BASE_DIR
    / "results"
    / "predictions_noisy_raw.jsonl"
)

PREPROCESSED_FILE = (
    BASE_DIR
    / "results"
    / "predictions_noisy_preprocessed.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "results"
    / "noise_ab_metrics.json"
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
            return (
                float(expected)
                == float(predicted)
            )
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
            expected_item.get(
                "material_text"
            ),
            predicted_item.get(
                "material_text"
            ),
        ):
            material_correct = False

        if not values_match(
            expected_item.get(
                "quantity"
            ),
            predicted_item.get(
                "quantity"
            ),
        ):
            quantity_correct = False

        if not values_match(
            expected_item.get(
                "unit_text"
            ),
            predicted_item.get(
                "unit_text"
            ),
        ):
            unit_correct = False

    return {
        "material_correct": (
            material_correct
        ),
        "quantity_correct": (
            quantity_correct
        ),
        "unit_correct": (
            unit_correct
        ),
        "all_correct": (
            material_correct
            and quantity_correct
            and unit_correct
        ),
    }


def percent(
    correct: int,
    total: int,
):
    if total == 0:
        return None

    return round(
        correct / total * 100,
        2,
    )


def evaluate_predictions(
    ground_truth: dict,
    predictions: list[dict],
) -> dict:
    stats = {
        "total_cases": 0,
        "successful_cases": 0,
        "material_cases": 0,
        "word_errors": 0,
        "reference_words": 0,
        "activity_correct": 0,
        "lot_correct": 0,
        "material_correct": 0,
        "quantity_correct": 0,
        "unit_correct": 0,
        "time_correct": 0,
        "full_record_correct": 0,
        "processing_time_ms": 0.0,
    }

    cases = []

    for result in predictions:
        test_case_id = result[
            "test_case_id"
        ]

        expected = ground_truth.get(
            test_case_id
        )

        if expected is None:
            continue

        stats["total_cases"] += 1

        if not result.get("success"):
            cases.append({
                "test_case_id": (
                    test_case_id
                ),
                "success": False,
            })

            continue

        stats["successful_cases"] += 1

        prediction = result[
            "prediction"
        ]

        transcript = prediction[
            "transcript"
        ]

        structured = prediction[
            "structured_data"
        ]

        word_errors, reference_words = (
            calculate_wer(
                expected[
                    "ground_truth_transcript"
                ],
                transcript,
            )
        )

        stats["word_errors"] += (
            word_errors
        )

        stats["reference_words"] += (
            reference_words
        )

        activity_correct = values_match(
            expected.get(
                "activity_text"
            ),
            structured.get(
                "activity_text"
            ),
        )

        lot_correct = values_match(
            expected.get(
                "lot_text"
            ),
            structured.get(
                "lot_text"
            ),
        )

        time_correct = values_match(
            expected.get(
                "time_text"
            ),
            structured.get(
                "time_text"
            ),
        )

        expected_materials = (
            expected.get(
                "materials",
                [],
            )
        )

        predicted_materials = (
            structured.get(
                "materials",
                [],
            )
        )

        material_result = (
            compare_materials(
                expected_materials,
                predicted_materials,
            )
        )

        has_material = bool(
            expected_materials
        )

        full_record_correct = (
            activity_correct
            and lot_correct
            and time_correct
            and material_result[
                "all_correct"
            ]
        )

        if activity_correct:
            stats[
                "activity_correct"
            ] += 1

        if lot_correct:
            stats[
                "lot_correct"
            ] += 1

        if time_correct:
            stats[
                "time_correct"
            ] += 1

        if full_record_correct:
            stats[
                "full_record_correct"
            ] += 1

        if has_material:
            stats[
                "material_cases"
            ] += 1

            if material_result[
                "material_correct"
            ]:
                stats[
                    "material_correct"
                ] += 1

            if material_result[
                "quantity_correct"
            ]:
                stats[
                    "quantity_correct"
                ] += 1

            if material_result[
                "unit_correct"
            ]:
                stats[
                    "unit_correct"
                ] += 1

        total_time_ms = (
            result
            .get("timing", {})
            .get(
                "total_time_ms",
                0,
            )
        )

        stats[
            "processing_time_ms"
        ] += total_time_ms

        case_wer = (
            word_errors
            / reference_words
            * 100
            if reference_words
            else 0
        )

        cases.append({
            "test_case_id": (
                test_case_id
            ),
            "wer_percent": round(
                case_wer,
                2,
            ),
            "activity_correct": (
                activity_correct
            ),
            "lot_correct": (
                lot_correct
            ),
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
            "time_correct": (
                time_correct
            ),
            "full_record_correct": (
                full_record_correct
            ),
            "processing_time_ms": (
                total_time_ms
            ),
        })

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
        average_processing_time_ms = (
            round(
                stats[
                    "processing_time_ms"
                ]
                / stats[
                    "successful_cases"
                ],
                2,
            )
        )
    else:
        average_processing_time_ms = None

    metrics = {
        "total_cases": (
            stats["total_cases"]
        ),
        "successful_cases": (
            stats["successful_cases"]
        ),
        "wer_percent": (
            wer_percent
        ),
        "activity_accuracy_percent": (
            percent(
                stats[
                    "activity_correct"
                ],
                stats[
                    "total_cases"
                ],
            )
        ),
        "lot_accuracy_percent": (
            percent(
                stats[
                    "lot_correct"
                ],
                stats[
                    "total_cases"
                ],
            )
        ),
        "material_accuracy_percent": (
            percent(
                stats[
                    "material_correct"
                ],
                stats[
                    "material_cases"
                ],
            )
        ),
        "quantity_accuracy_percent": (
            percent(
                stats[
                    "quantity_correct"
                ],
                stats[
                    "material_cases"
                ],
            )
        ),
        "unit_accuracy_percent": (
            percent(
                stats[
                    "unit_correct"
                ],
                stats[
                    "material_cases"
                ],
            )
        ),
        "time_accuracy_percent": (
            percent(
                stats[
                    "time_correct"
                ],
                stats[
                    "total_cases"
                ],
            )
        ),
        "full_record_accuracy_percent": (
            percent(
                stats[
                    "full_record_correct"
                ],
                stats[
                    "total_cases"
                ],
            )
        ),
        "average_processing_time_ms": (
            average_processing_time_ms
        ),
    }

    return {
        "metrics": metrics,
        "cases": cases,
    }


def format_percent(value) -> str:
    if value is None:
        return "N/A"

    return f"{value}%"


def format_ms(value) -> str:
    if value is None:
        return "N/A"

    return f"{value} ms"


def print_comparison(
    raw: dict,
    preprocessed: dict,
) -> None:
    raw_metrics = raw["metrics"]
    pre_metrics = (
        preprocessed["metrics"]
    )

    print("=" * 78)
    print(
        "NEXTFARM VOICELOG - "
        "NOISE A/B EVALUATION"
    )
    print("=" * 78)

    print(
        f"{'Metric':<30}"
        f"{'RAW':>20}"
        f"{'FFMPEG ON':>20}"
    )

    print("-" * 78)

    rows = [
        (
            "WER",
            "wer_percent",
            "percent",
        ),
        (
            "Activity Accuracy",
            "activity_accuracy_percent",
            "percent",
        ),
        (
            "Lot Accuracy",
            "lot_accuracy_percent",
            "percent",
        ),
        (
            "Material Accuracy",
            "material_accuracy_percent",
            "percent",
        ),
        (
            "Quantity Accuracy",
            "quantity_accuracy_percent",
            "percent",
        ),
        (
            "Unit Accuracy",
            "unit_accuracy_percent",
            "percent",
        ),
        (
            "Time Accuracy",
            "time_accuracy_percent",
            "percent",
        ),
        (
            "Full Record Accuracy",
            "full_record_accuracy_percent",
            "percent",
        ),
        (
            "Average Processing Time",
            "average_processing_time_ms",
            "ms",
        ),
    ]

    for label, key, value_type in rows:
        raw_value = raw_metrics[key]
        pre_value = pre_metrics[key]

        if value_type == "percent":
            raw_display = (
                format_percent(
                    raw_value
                )
            )

            pre_display = (
                format_percent(
                    pre_value
                )
            )

        else:
            raw_display = (
                format_ms(
                    raw_value
                )
            )

            pre_display = (
                format_ms(
                    pre_value
                )
            )

        print(
            f"{label:<30}"
            f"{raw_display:>20}"
            f"{pre_display:>20}"
        )


def print_case_comparison(
    raw: dict,
    preprocessed: dict,
) -> None:
    raw_cases = {
        case["test_case_id"]: case
        for case in raw["cases"]
    }

    pre_cases = {
        case["test_case_id"]: case
        for case in preprocessed["cases"]
    }

    print("\n" + "=" * 78)
    print("PER-CASE FULL RECORD")
    print("=" * 78)

    for test_case_id in sorted(
        raw_cases.keys()
    ):
        raw_case = raw_cases[
            test_case_id
        ]

        pre_case = pre_cases.get(
            test_case_id
        )

        if not pre_case:
            continue

        raw_full = raw_case.get(
            "full_record_correct"
        )

        pre_full = pre_case.get(
            "full_record_correct"
        )

        raw_label = (
            "PASS"
            if raw_full
            else "FAIL"
        )

        pre_label = (
            "PASS"
            if pre_full
            else "FAIL"
        )

        if (
            raw_full is False
            and pre_full is True
        ):
            change = "IMPROVED"
        elif (
            raw_full is True
            and pre_full is False
        ):
            change = "REGRESSED"
        else:
            change = "UNCHANGED"

        print(
            f"{test_case_id}: "
            f"RAW={raw_label} | "
            f"FFMPEG={pre_label} | "
            f"{change}"
        )


def main() -> None:
    ground_truth_rows = load_jsonl(
        GROUND_TRUTH_FILE
    )

    noisy_ground_truth = {
        row["test_case_id"]: row
        for row in ground_truth_rows
        if row.get(
            "environment"
        ) == "noisy"
    }

    raw_predictions = load_jsonl(
        RAW_FILE
    )

    preprocessed_predictions = (
        load_jsonl(
            PREPROCESSED_FILE
        )
    )

    raw_results = (
        evaluate_predictions(
            noisy_ground_truth,
            raw_predictions,
        )
    )

    preprocessed_results = (
        evaluate_predictions(
            noisy_ground_truth,
            preprocessed_predictions,
        )
    )

    output = {
        "noise_type": (
            "synthetic_white"
        ),
        "raw": raw_results,
        "preprocessed": (
            preprocessed_results
        ),
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print_comparison(
        raw_results,
        preprocessed_results,
    )

    print_case_comparison(
        raw_results,
        preprocessed_results,
    )

    print(
        f"\nMetrics file: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()