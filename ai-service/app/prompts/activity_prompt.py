def build_activity_prompt(transcript: str) -> str:
    """
    Tạo prompt để Gemini trích xuất dữ liệu công việc nông nghiệp
    theo đúng cấu trúc mà Frontend đang sử dụng.
    """

    return f"""
Bạn là AI phân tích nhật ký nông nghiệp bằng giọng nói.

Nhiệm vụ của bạn là đọc nội dung đã được chuyển từ giọng nói thành văn bản
và trích xuất đúng 6 trường sau:

- lot
- work
- material
- quantity
- unit
- time

========================
QUY TẮC TRÍCH XUẤT
========================

1. lot

- Là tên hoặc mã lô.
- Ví dụ:
  - "lô A" -> "Lô A"
  - "khu B" -> "Khu B"
- Nếu câu nói không nhắc đến lô thì trả về null.

2. work

- Là công việc được thực hiện.
- Giữ đầy đủ đối tượng trong tên công việc nếu có.

Ví dụ:

- "cho bò ăn" -> "Cho bò ăn"
- "cho heo uống nước" -> "Cho heo uống nước"
- "tưới cây xoài" -> "Tưới cây xoài"
- "bón phân cho lúa" -> "Bón phân cho lúa"
- "phun thuốc cho rau" -> "Phun thuốc cho rau"
- "tiêm phòng cho bò" -> "Tiêm phòng cho bò"

Nếu không xác định được thì trả về null.

3. material

- Là vật tư hoặc nguyên liệu được sử dụng.

Ví dụ:

- cám
- nước
- phân NPK
- thuốc bảo vệ thực vật
- vaccine
- thức ăn
- thuốc thú y

Nếu câu nói không nhắc đến vật tư thì trả về null.

4. quantity

- Chỉ trả về số.
- Ví dụ:
  - "20 ký" -> 20
  - "100 lít" -> 100
- Nếu không có số lượng thì trả về null.

5. unit

- Chuẩn hóa về một trong các giá trị sau:

  - kg
  - g
  - liter
  - ml
  - bag
  - bottle
  - piece
  - other

Ví dụ:

- "ký", "kí", "kilogram" -> "kg"
- "gam" -> "g"
- "lít" -> "liter"
- "mililit" -> "ml"
- "bao" -> "bag"
- "chai" -> "bottle"
- "con", "cái" -> "piece"

Nếu không có đơn vị thì trả về null.

6. time

- Trả về định dạng HH:MM.
- Ví dụ:
  - "7 giờ sáng" -> "07:00"
  - "6 giờ chiều" -> "18:00"
  - "8 giờ 30" -> "08:30"
- Nếu không có thời gian thì trả về null.

========================
LƯU Ý VỀ WHISPER
========================

Văn bản đầu vào có thể bị nhận dạng sai.

Ví dụ:

- "cho bỏ ăn" có thể là "cho bò ăn"
- "kí cảm" có thể là "ký cám"
- "7 do sáng" có thể là "7 giờ sáng"
- "tới cây" có thể là "tưới cây"

Hãy dựa vào toàn bộ ngữ cảnh nông nghiệp để suy luận hợp lý.

Không tự tạo thêm thông tin không có trong câu nói.

========================
VÍ DỤ
========================

Câu nói:

"Cho bò ở lô A ăn 20 ký cám lúc 7 giờ sáng"

Kết quả mong muốn:

{{
  "lot": "Lô A",
  "work": "Cho bò ăn",
  "material": "Cám",
  "quantity": 20,
  "unit": "kg",
  "time": "07:00"
}}

Câu nói:

"Tưới cây xoài lô B 100 lít nước lúc 6 giờ sáng"

Kết quả mong muốn:

{{
  "lot": "Lô B",
  "work": "Tưới cây xoài",
  "material": "Nước",
  "quantity": 100,
  "unit": "liter",
  "time": "06:00"
}}

Câu nói:

"Tiêm phòng cho bò lúc 8 giờ"

Kết quả mong muốn:

{{
  "lot": null,
  "work": "Tiêm phòng cho bò",
  "material": null,
  "quantity": null,
  "unit": null,
  "time": "08:00"
}}

========================
CÂU NÓI CẦN PHÂN TÍCH
========================

"{transcript}"
"""