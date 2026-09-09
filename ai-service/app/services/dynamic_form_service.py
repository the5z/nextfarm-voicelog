from typing import Any

from google import genai
from google.genai.errors import APIError

from app.core.config import settings
from app.prompts.dynamic_form_prompt import build_dynamic_form_prompt
from app.schemas.dynamic_form import (
    DynamicFormResponse,
    RESPONSE_MODEL_BY_OPERATION,
)


client = genai.Client(api_key=settings.GEMINI_API_KEY)


def extract_dynamic_form(
    operation: str,
    transcript: str,
    current_fields: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> DynamicFormResponse:
    response_model = RESPONSE_MODEL_BY_OPERATION.get(operation)

    if response_model is None:
        raise ValueError(f"Unsupported operation: {operation}")

    prompt = build_dynamic_form_prompt(
        operation=operation,
        transcript=transcript,
        current_fields=current_fields,
        context=context,
    )

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": response_model,
                "temperature": 0,
            },
        )

        if response.parsed is None:
            raise ValueError(
                "Gemini returned no structured dynamic form data."
            )

        return response.parsed

    except APIError as exc:
        raise RuntimeError(
            f"Gemini API error while extracting dynamic form: {exc}"
        ) from exc