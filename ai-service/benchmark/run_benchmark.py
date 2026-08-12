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
PREDICTIONS_FILE = RESULTS_DIR / "predictions.jsonl"


def load_dataset() -> list[dict]:
    rows = []

    with GROUND_TRUTH_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            rows.append(json.loads(line))

    return rows


def run_test_case(test_case: dict) -> dict:
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
        print(f"\n[{test_case_id}] Processing: {audio_file}")

        preprocess_started = time.perf_counter()

        cleaned_audio_path = reduce_noise(audio_path)

        preprocessing_time_ms = round(
            (time.perf_counter() - preprocess_started) * 1000,
            2,
        )

        whisper_started = time.perf_counter()

        transcript = transcribe_audio(cleaned_audio_path)

        whisper_time_ms = round(
            (time.perf_counter() - whisper_started) * 1000,
            2,
        )

        gemini_started = time.perf_counter()

        structured_data = extract_activity(transcript)

        gemini_time_ms = round(
            (time.perf_counter() - gemini_started) * 1000,
            2,
        )

        total_time_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        prediction = {
            "test_case_id": test_case_id,
            "audio_file": audio_file,
            "success": True,
            "prediction": {
                "transcript": transcript,
                "structured_data": structured_data.model_dump(),
            },
            "timing": {
                "preprocessing_time_ms": preprocessing_time_ms,
                "whisper_time_ms": whisper_time_ms,
                "gemini_time_ms": gemini_time_ms,
                "total_time_ms": total_time_ms,
            },
            "error": None,
        }

        print(f"[{test_case_id}] Transcript: {transcript}")
        print(
            f"[{test_case_id}] Total time: "
            f"{total_time_ms} ms"
        )

        return prediction

    except Exception as exc:
        total_time_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2,
        )

        print(f"[{test_case_id}] ERROR: {exc}")

        return {
            "test_case_id": test_case_id,
            "audio_file": audio_file,
            "success": False,
            "prediction": None,
            "timing": {
                "total_time_ms": total_time_ms,
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


def save_predictions(predictions: list[dict]) -> None:
    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with PREDICTIONS_FILE.open(
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


def main() -> None:
    dataset = load_dataset()

    print("=" * 60)
    print("NEXTFARM VOICELOG - AI BENCHMARK")
    print("=" * 60)
    print(f"Total test cases: {len(dataset)}")

    predictions = []

    for test_case in dataset:
        result = run_test_case(test_case)
        predictions.append(result)

    save_predictions(predictions)

    successful = sum(
        1
        for result in predictions
        if result["success"]
    )

    failed = len(predictions) - successful

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETED")
    print("=" * 60)
    print(f"Total:   {len(predictions)}")
    print(f"Success: {successful}")
    print(f"Failed:  {failed}")
    print(f"Output:  {PREDICTIONS_FILE}")


if __name__ == "__main__":
    main()