import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

GROUND_TRUTH_PATH = BASE_DIR / "ground_truth" / "dataset.jsonl"
PREDICTIONS_PATH = BASE_DIR / "results" / "predictions_confirmation_cases.jsonl"
OUTPUT_PATH = BASE_DIR / "results" / "confirmation_metrics.json"


def load_jsonl(path: Path) -> list[dict]:
    rows = []

    with path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def normalize_fields(fields: list[str] | None) -> set[str]:
    return set(fields or [])


def main() -> None:
    ground_truth_rows = load_jsonl(GROUND_TRUTH_PATH)
    prediction_rows = load_jsonl(PREDICTIONS_PATH)

    ground_truth_by_id = {
        row["test_case_id"]: row
        for row in ground_truth_rows
    }

    total_cases = 0
    correct_accept = 0
    correct_confirmation = 0
    unsafe_guess = 0
    unnecessary_confirmation = 0

    positive_cases = 0
    detected_positive_cases = 0

    missing_fields_exact_match = 0

    case_results = []

    for prediction_row in prediction_rows:
        test_case_id = prediction_row["test_case_id"]

        ground_truth = ground_truth_by_id.get(test_case_id)

        if ground_truth is None:
            print(f"[SKIP] Ground truth not found: {test_case_id}")
            continue

        if not prediction_row.get("success"):
            print(f"[FAIL] Pipeline failed: {test_case_id}")
            continue

        structured_data = prediction_row["prediction"]["structured_data"]

        expected_confirmation = bool(
            ground_truth.get("expected_confirmation", False)
        )

        predicted_confirmation = bool(
            structured_data.get("requires_confirmation", False)
        )

        expected_missing_fields = normalize_fields(
            ground_truth.get("expected_missing_fields")
        )

        predicted_missing_fields = normalize_fields(
            structured_data.get("missing_fields")
        )

        total_cases += 1

        if expected_confirmation:
            positive_cases += 1

        if expected_confirmation and predicted_confirmation:
            category = "correct_confirmation"
            correct_confirmation += 1
            detected_positive_cases += 1

        elif not expected_confirmation and not predicted_confirmation:
            category = "correct_accept"
            correct_accept += 1

        elif expected_confirmation and not predicted_confirmation:
            category = "unsafe_guess"
            unsafe_guess += 1

        else:
            category = "unnecessary_confirmation"
            unnecessary_confirmation += 1

        missing_match = (
            expected_missing_fields == predicted_missing_fields
        )

        if missing_match:
            missing_fields_exact_match += 1

        case_result = {
            "test_case_id": test_case_id,
            "confirmation_category": ground_truth.get(
                "confirmation_category"
            ),
            "expected_confirmation": expected_confirmation,
            "predicted_confirmation": predicted_confirmation,
            "result": category,
            "expected_missing_fields": sorted(
                expected_missing_fields
            ),
            "predicted_missing_fields": sorted(
                predicted_missing_fields
            ),
            "missing_fields_exact_match": missing_match,
            "warnings": structured_data.get("warnings", []),
        }

        case_results.append(case_result)

    correct_decisions = correct_accept + correct_confirmation

    confirmation_accuracy = (
        correct_decisions / total_cases
        if total_cases
        else 0.0
    )

    confirmation_recall = (
        detected_positive_cases / positive_cases
        if positive_cases
        else 0.0
    )

    unsafe_guess_rate = (
        unsafe_guess / positive_cases
        if positive_cases
        else 0.0
    )

    missing_fields_exact_match_rate = (
        missing_fields_exact_match / total_cases
        if total_cases
        else 0.0
    )

    metrics = {
        "total_cases": total_cases,
        "correct_accept": correct_accept,
        "correct_confirmation": correct_confirmation,
        "unsafe_guess": unsafe_guess,
        "unnecessary_confirmation": unnecessary_confirmation,
        "confirmation_accuracy": round(
            confirmation_accuracy * 100,
            2,
        ),
        "confirmation_recall": round(
            confirmation_recall * 100,
            2,
        ),
        "unsafe_guess_rate": round(
            unsafe_guess_rate * 100,
            2,
        ),
        "missing_fields_exact_match_rate": round(
            missing_fields_exact_match_rate * 100,
            2,
        ),
        "cases": case_results,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=== Confirmation Evaluation ===")
    print(f"Total cases: {total_cases}")
    print(f"Correct Accept: {correct_accept}")
    print(
        f"Correct Confirmation: "
        f"{correct_confirmation}"
    )
    print(f"Unsafe Guess: {unsafe_guess}")
    print(
        f"Unnecessary Confirmation: "
        f"{unnecessary_confirmation}"
    )
    print(
        f"Confirmation Accuracy: "
        f"{metrics['confirmation_accuracy']}%"
    )
    print(
        f"Confirmation Recall: "
        f"{metrics['confirmation_recall']}%"
    )
    print(
        f"Unsafe Guess Rate: "
        f"{metrics['unsafe_guess_rate']}%"
    )
    print(
        "Missing Fields Exact Match: "
        f"{metrics['missing_fields_exact_match_rate']}%"
    )

    print()
    print("=== Per Case ===")

    for case in case_results:
        print(
            f"{case['test_case_id']} | "
            f"{case['result']} | "
            f"missing_match="
            f"{case['missing_fields_exact_match']}"
        )

    print()
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()