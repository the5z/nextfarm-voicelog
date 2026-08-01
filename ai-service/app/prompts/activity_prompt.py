def build_activity_prompt(transcript: str) -> str:
    """
    Build the prompt used to extract structured livestock activity data.
    """

    return f"""
Bạn là AI phân tích nhật ký chăn nuôi.

Nhiệm vụ của bạn là đọc nội dung ghi âm đã được chuyển thành văn bản
và trích xuất dữ liệu dưới dạng JSON.

========================
QUY TẮC
========================

activity chỉ được chọn một trong:

- feeding
- watering
- milking
- vaccination
- health_check
- breeding
- cleaning
- weighing
- treatment
- other


animal chỉ được chọn một trong:

- cow
- pig
- chicken
- duck
- goat
- sheep
- buffalo
- other


quantity

- chỉ trả về số
- nếu không có thì null


unit

chỉ được chọn:

- kg
- g
- liter
- ml
- bag
- bottle
- piece
- other


time

- trả về định dạng HH:MM
- nếu không có thì null


note

- thông tin còn lại
- nếu không có thì null


========================
LƯU Ý
========================

Whisper có thể nhận dạng sai một số từ.

Ví dụ:

- "cho bỏ ăn" -> "cho bò ăn"
- "kí cảm" -> "ký cám"
- "7 do sáng" -> "7 giờ sáng"

Hãy ưu tiên suy luận theo ngữ cảnh chăn nuôi.

Chỉ trả về "other" nếu thật sự không thể xác định.


========================
CÂU NÓI
========================

"{transcript}"
"""