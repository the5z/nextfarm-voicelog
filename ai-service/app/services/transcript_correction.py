import re


SAFE_CORRECTIONS: list[tuple[str, str]] = [
    # Urê
    (
        r"\bU[-\s]?Ray\b",
        "urê",
    ),
    (
        r"\bU[-\s]?Re\b",
        "urê",
    ),
    (
        r"\bU[-\s]?Rê\b",
        "urê",
    ),
    (
        r"\bure\b",
        "urê",
    ),

    # NPK khi Whisper vẫn giữ được các chữ cái.
    (
        r"\bN[\s.-]?P[\s.-]?K\b",
        "NPK",
    ),

    # Một số lỗi STT phổ biến, ít mơ hồ.
    (
        r"\bđá hoàn thành\b",
        "đã hoàn thành",
    ),
    (
        r"\bthú hoạch\b",
        "thu hoạch",
    ),
]


def _correct_contextual_npk(
    text: str,
) -> str:
    """
    Correct likely NPK transcription errors only when
    agricultural/fertilizer context makes the meaning clear.
    """

    fertilizer_context = re.search(
        r"\b("
        r"bón|"
        r"phân|"
        r"phân bón|"
        r"bón phân|"
        r"vật tư"
        r")\b",
        text,
        flags=re.IGNORECASE,
    )

    if not fertilizer_context:
        return text

    patterns = [
        r"\ben[\s.-]*pê[\s.-]*ca\b",
        r"\ben[\s.-]*pê[\s.-]*ka\b",
        r"\bnờ[\s.-]*pê[\s.-]*ca\b",
        r"\bnờ[\s.-]*pê[\s.-]*ka\b",

        # Whisper đôi khi làm mất âm đầu.
        r"\bbé ca\b",
        r"\bpê ca\b",
        r"\bpê ka\b",
    ]

    corrected = text

    for pattern in patterns:
        corrected = re.sub(
            pattern,
            "NPK",
            corrected,
            flags=re.IGNORECASE,
        )

    return corrected


def _correct_contextual_weight(
    text: str,
) -> str:
    """
    Normalize expressions such as '120k' to '120 kg'
    only when the sentence clearly describes agricultural
    quantity/weight.

    This avoids converting values such as prices or money.
    """

    agricultural_context = re.search(
        r"\b("
        r"thu hoạch|"
        r"sản lượng|"
        r"năng suất|"
        r"bón|"
        r"phân|"
        r"vật tư|"
        r"giống|"
        r"thu được|"
        r"được"
        r")\b",
        text,
        flags=re.IGNORECASE,
    )

    if not agricultural_context:
        return text

    corrected = re.sub(
        r"\b(\d+(?:[.,]\d+)?)\s*k\b",
        r"\1 kg",
        text,
        flags=re.IGNORECASE,
    )

    return corrected


def correct_transcript(
    text: str,
) -> str:
    if not text:
        return ""

    corrected = text.strip()

    for pattern, replacement in SAFE_CORRECTIONS:
        corrected = re.sub(
            pattern,
            replacement,
            corrected,
            flags=re.IGNORECASE,
        )

    corrected = _correct_contextual_npk(
        corrected
    )

    corrected = _correct_contextual_weight(
        corrected
    )

    corrected = re.sub(
        r"\s+",
        " ",
        corrected,
    )

    return corrected.strip()