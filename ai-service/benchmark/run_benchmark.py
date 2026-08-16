import argparse
import json
import time
from pathlib import Path

from app.services.audio_preprocessing import reduce_noise
from app.services.transcribe import transcribe_audio
from app.services.llm_service import extract_activity


BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio"
GROUND_TRUTH_FILE = BASE_DIR / "ground_truth" / "dataset.jsonl"
RESULTS_DIR = BASE_DIR / "results"


def parse_args():
    parser = argparse.ArgumentParser(
        description="NextFarm VoiceLog benchmark runner"
    )

    parser.add_argument(
        "--preprocess",
        choices=["on", "off"],
        default="on",
        help=(
            "Enable or disable FFmpeg audio preprocessing. "
            "Default: on"
        ),
    )

    parser.add_argument(
        "--environment",
        choices=["all", "clean", "noisy"],
        default="all",
        help=(
            "Select dataset environment to benchmark. "
            "Default: all"
        ),
    )

    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Optional output filename inside benchmark/results. "
            "Example: predictions_noisy_raw.jsonl"
        ),
    )

    return parser.parse_args()


def load_dataset(
    environment: str = "all",
) -> list[dict]:
    rows = []

    with GROUND_TRUTH_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            row = json.loads(line)

            if (
                environment != "all"
                and row.get("environment")
                != environment
            ):
                continue

            rows.append(row)

    return rows


def run_test_case(
    test_case: dict,
    use_preprocessing: bool,
) -> dict:
    test_case_id = test_case["test_case_id"]
    audio_file = test_case["audio_file"]
    audio_path = AUDIO_DIR / audio_file

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    cleaned_audio_path = None
    started_at = time.perf_counter()

    try:
        print(
            f"\n[{test_case_id}] Processing: "
            f"{audio_file}"
        )

        print(
            f"[{test_case_id}] Preprocessing: "
            f"{'ON' if use_preprocessing else 'OFF'}"
        )

        if use_preprocessing:
            preprocess_started = (
                time.perf_counter()
            )

            cleaned_audio_path = reduce_noise(
                audio_path
            )

            preprocessing_time_ms = round(
                (
                    time.perf_counter()
                    - preprocess_started
                )
                * 1000,
                2,
            )

            transcription_input = (
                cleaned_audio_path
            )

        else:
            preprocessing_time_ms = 0.0
            transcription_input = audio_path

        whisper_started = time.perf_counter()

        transcript = transcribe_audio(
            transcription_input
        )

        whisper_time_ms = round(
            (
                time.perf_counter()
                - whisper_started
            )
            * 1000,
            2,
        )

        gemini_started = time.perf_counter()

        structured_data = extract_activity(
            transcript
        )

        gemini_time_ms = round(
            (
                time.perf_counter()
                - gemini_started
            )
            * 1000,
            2,
        )

        total_time_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

        prediction = {
            "test_case_id": test_case_id,
            "audio_file": audio_file,
            "success": True,
            "benchmark_config": {
                "preprocessing_enabled": (
                    use_preprocessing
                ),
                "environment": (
                    test_case.get(
                        "environment"
                    )
                ),
            },
            "prediction": {
                "transcript": transcript,
                "structured_data": (
                    structured_data.model_dump()
                ),
            },
            "timing": {
                "preprocessing_time_ms": (
                    preprocessing_time_ms
                ),
                "whisper_time_ms": (
                    whisper_time_ms
                ),
                "gemini_time_ms": (
                    gemini_time_ms
                ),
                "total_time_ms": (
                    total_time_ms
                ),
            },
            "error": None,
        }

        print(
            f"[{test_case_id}] Transcript: "
            f"{transcript}"
        )

        print(
            f"[{test_case_id}] "
            f"Preprocessing time: "
            f"{preprocessing_time_ms} ms"
        )

        print(
            f"[{test_case_id}] "
            f"Whisper time: "
            f"{whisper_time_ms} ms"
        )

        print(
            f"[{test_case_id}] "
            f"Gemini time: "
            f"{gemini_time_ms} ms"
        )

        print(
            f"[{test_case_id}] "
            f"Total time: "
            f"{total_time_ms} ms"
        )

        return prediction

    except Exception as exc:
        total_time_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            2,
        )

        print(
            f"[{test_case_id}] ERROR: {exc}"
        )

        return {
            "test_case_id": test_case_id,
            "audio_file": audio_file,
            "success": False,
            "benchmark_config": {
                "preprocessing_enabled": (
                    use_preprocessing
                ),
                "environment": (
                    test_case.get(
                        "environment"
                    )
                ),
            },
            "prediction": None,
            "timing": {
                "total_time_ms": (
                    total_time_ms
                ),
            },
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }

    finally:
        if (
            cleaned_audio_path is not None
            and cleaned_audio_path.exists()
        ):
            cleaned_audio_path.unlink()


def save_predictions(
    predictions: list[dict],
    output_file: Path,
) -> None:
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        for prediction in predictions:
            file.write(
                json.dumps(
                    prediction,
                    ensure_ascii=False,
                )
                + "\n"
            )


def resolve_output_file(
    output_name: str | None,
    environment: str,
    use_preprocessing: bool,
) -> Path:
    if output_name:
        return RESULTS_DIR / output_name

    preprocessing_label = (
        "preprocessed"
        if use_preprocessing
        else "raw"
    )

    filename = (
        f"predictions_"
        f"{environment}_"
        f"{preprocessing_label}.jsonl"
    )

    return RESULTS_DIR / filename


def main() -> None:
    args = parse_args()

    use_preprocessing = (
        args.preprocess == "on"
    )

    dataset = load_dataset(
        environment=args.environment,
    )

    output_file = resolve_output_file(
        output_name=args.output,
        environment=args.environment,
        use_preprocessing=use_preprocessing,
    )

    print("=" * 60)
    print(
        "NEXTFARM VOICELOG - AI BENCHMARK"
    )
    print("=" * 60)

    print(
        f"Environment: "
        f"{args.environment}"
    )

    print(
        f"Preprocessing: "
        f"{'ON' if use_preprocessing else 'OFF'}"
    )

    print(
        f"Total test cases: "
        f"{len(dataset)}"
    )

    print(
        f"Output file: "
        f"{output_file}"
    )

    predictions = []

    for test_case in dataset:
        result = run_test_case(
            test_case,
            use_preprocessing=(
                use_preprocessing
            ),
        )

        predictions.append(result)

    save_predictions(
        predictions,
        output_file,
    )

    successful = sum(
        1
        for result in predictions
        if result["success"]
    )

    failed = (
        len(predictions)
        - successful
    )

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETED")
    print("=" * 60)

    print(
        f"Total:   "
        f"{len(predictions)}"
    )

    print(
        f"Success: "
        f"{successful}"
    )

    print(
        f"Failed:  "
        f"{failed}"
    )

    print(
        f"Output:  "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()