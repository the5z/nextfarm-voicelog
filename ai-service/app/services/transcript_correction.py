import re


SAFE_CORRECTIONS: list[tuple[str, str]] = [
    (
        r"\bU[-\s]?Ray\b",
        "urê",
    ),
    (
        r"\bU[-\s]?Re\b",
        "urê",
    ),
    (
        r"\bN[\s.-]?P[\s.-]?K\b",
        "NPK",
    ),
]


def correct_transcript(
    text: str,
) -> str:
    corrected = text

    for pattern, replacement in SAFE_CORRECTIONS:
        corrected = re.sub(
            pattern,
            replacement,
            corrected,
            flags=re.IGNORECASE,
        )

    return corrected.strip()