import os

from dotenv import load_dotenv
from google import genai

from app.schemas.activity import ActivityData


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Please add it to the .env file."
    )

client = genai.Client(api_key=api_key)


def extract_activity(transcript: str) -> ActivityData:
    prompt = f"""
Bạn là hệ thống phân tích nhật ký chăn nuôi.

Hãy phân tích câu nói sau và trả về dữ liệu JSON theo các trường:

- activity: loại hoạt động bằng tiếng Anh, ví dụ feeding, vaccination, milking, health_check
- animal: loại vật nuôi bằng tiếng Anh
- quantity: số lượng nếu có
- unit: đơn vị nếu có
- time: thời gian theo định dạng HH:MM nếu có
- note: thông tin bổ sung nếu có

Câu nói:
"{transcript}"
"""

    response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ActivityData,
            "temperature": 0,
        },
    )

    if response.parsed is None:
        raise ValueError("Gemini did not return valid structured data.")

    return response.parsed