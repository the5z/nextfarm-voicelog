from google import genai
from google.genai import errors

from app.core.config import settings
from app.prompts.activity_prompt import build_activity_prompt
from app.schemas.activity import ActivityData
from app.services.confidence_service import apply_confidence_rules


if not settings.GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Please add it to the .env file."
    )


client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def extract_activity(transcript: str) -> ActivityData:
    """
    Analyze an agricultural voice log and return structured text data.

    This service only extracts human-readable values.
    Business codes are resolved later by the Integration Service.
    """

    prompt = build_activity_prompt(
        transcript
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ActivityData,
                "temperature": 0,
            },
        )

        if response.parsed is None:
            raise ValueError(
                "Gemini returned an empty structured response."
            )

        return apply_confidence_rules(
            response.parsed
        )

    except errors.APIError as exc:
        raise RuntimeError(
            f"Gemini API error: {exc}"
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Activity extraction failed: {exc}"
        ) from exc