def build_activity_prompt(transcript: str) -> str:
    """
    Tạo prompt để Gemini trích xuất dữ liệu nhật ký nông nghiệp
    theo Contract V2.

    AI chỉ trả dữ liệu dạng văn bản dễ hiểu.
    Việc chuyển tên sang mã nghiệp vụ sẽ do Integration Service xử lý.
    """

    return f"""
Bạn là AI phân tích nhật ký nông nghiệp bằng giọng nói.

Nhiệm vụ của bạn là đọc nội dung đã được chuyển từ âm thanh thành văn bản
và trích xuất dữ liệu theo đúng cấu trúc sau:

- activity_text
- lot_text
- materials
- time_text

Không tự tạo mã nghiệp vụ như:

- activity_code
- lot_code
- material_code
- unit_code

Chỉ trả dữ liệu dạng văn bản dễ hiểu.

========================
CẤU TRÚC KẾT QUẢ
========================

{{
  "activity_text": "Tên hoạt động hoặc null",
  "lot_text": "Tên lô hoặc null",
  "materials": [
    {{
      "material_text": "Tên vật tư hoặc null",
      "quantity": 0,
      "unit_text": "Đơn vị hoặc null"
    }}
  ],
  "time_text": "HH:MM hoặc null"
}}

Nếu không có vật tư thì trả về:

"materials": []

========================
1. ACTIVITY_TEXT
========================

activity_text là tên hoạt động nông nghiệp dễ hiểu.

Ưu tiên chuẩn hóa về các tên sau nếu câu nói phù hợp:

- Bón phân
- Phun thuốc
- Tưới nước
- Làm cỏ
- Thu hoạch

Quy tắc chuẩn hóa:

- "bón phân", "rải phân", "cho phân", "đánh phân", "bỏ phân"
  -> "Bón phân"

- "phun thuốc", "xịt thuốc", "xịt sâu",
  "phun sâu", "phun thuốc sâu"
  -> "Phun thuốc"

- "tưới", "tưới nước", "tưới cây", "tưới ruộng"
  -> "Tưới nước"

- "làm cỏ", "nhổ cỏ", "dọn cỏ", "phát cỏ"
  -> "Làm cỏ"

- "thu hoạch", "hái", "hái trái", "hái quả", "cắt trái"
  -> "Thu hoạch"

Nếu câu nói thuộc hoạt động khác thì giữ tên hoạt động dễ hiểu,
không tự tạo mã viết hoa.

Nếu không xác định được hoạt động thì trả về null.

========================
2. LOT_TEXT
========================

lot_text là tên hoặc mã lô được nhắc trong câu.

Ví dụ:

- "lô A" -> "Lô A"
- "lô B" -> "Lô B"
- "khu số 2" -> "Khu số 2"
- "ruộng 3" -> "Ruộng 3"

Nếu câu nói không nhắc đến lô hoặc khu vực thì trả về null.

Không tự suy đoán lô nếu câu nói không có thông tin.

========================
3. MATERIALS
========================

materials là danh sách vật tư được sử dụng.

Mỗi vật tư gồm:

- material_text
- quantity
- unit_text

Ví dụ vật tư:

- Nước
- Phân NPK
- Thuốc sâu
- Thuốc bảo vệ thực vật
- Cám
- Phân hữu cơ

Nếu câu nói có nhiều vật tư thì trả về nhiều phần tử trong materials.

Ví dụ:

"bón 20 kg NPK và 10 kg phân hữu cơ"

Kết quả:

[
  {{
    "material_text": "NPK",
    "quantity": 20,
    "unit_text": "kg"
  }},
  {{
    "material_text": "Phân hữu cơ",
    "quantity": 10,
    "unit_text": "kg"
  }}
]

Nếu không có vật tư thì trả về danh sách rỗng:

[]

========================
4. QUANTITY
========================

quantity chỉ trả về số.

Ví dụ:

- "20 ký" -> 20
- "100 lít" -> 100
- "2 bao" -> 2
- "một trăm lít" -> 100

Nếu không có số lượng thì trả về null.

Không tự đoán số lượng.

========================
5. UNIT_TEXT
========================

unit_text là đơn vị dạng văn bản dễ hiểu.

Ưu tiên trả một trong các giá trị:

- kg
- g
- lít
- ml
- bao
- chai

Chuẩn hóa:

- "ký", "kí", "kilogram", "cân" -> "kg"
- "gam", "gram" -> "g"
- "l", "lit", "lít" -> "lít"
- "mililít", "mi li lít" -> "ml"
- "bịch", "túi", "bao" -> "bao"
- "lọ", "chai" -> "chai"

Với các đơn vị mơ hồ như:

- xị
- công
- sào

không tự quy đổi sang đơn vị khác.

Hãy giữ nguyên từ người dùng nói trong unit_text
để người dùng xác nhận sau.

Nếu không có đơn vị thì trả về null.

========================
6. TIME_TEXT
========================

time_text là thời gian theo định dạng HH:MM.

Ví dụ:

- "7 giờ sáng" -> "07:00"
- "6 giờ chiều" -> "18:00"
- "8 giờ 30" -> "08:30"
- "9 giờ tối" -> "21:00"

Nếu không có thời gian thì trả về null.

Không tự thêm ngày tháng.

========================
LƯU Ý VỀ WHISPER
========================

Transcript có thể chứa lỗi nhận dạng.

Ví dụ:

- "tử ý" có thể là "tưới"
- "kê sòi" có thể là "cây xoài"
- "lý nước" có thể là "lít nước"
- "sấu giờ sáng" có thể là "sáu giờ sáng"
- "bỏ phân" có thể là "bón phân"
- "phun sâu" có thể là "phun thuốc sâu"

Hãy dựa vào toàn bộ ngữ cảnh nông nghiệp để suy luận hợp lý.

Không tự tạo thêm thông tin không có trong câu nói.

========================
VÍ DỤ 1
========================

Câu nói:

"Bón phân lô A 20 ký NPK lúc 7 giờ sáng"

Kết quả mong muốn:

{{
  "activity_text": "Bón phân",
  "lot_text": "Lô A",
  "materials": [
    {{
      "material_text": "NPK",
      "quantity": 20,
      "unit_text": "kg"
    }}
  ],
  "time_text": "07:00"
}}

========================
VÍ DỤ 2
========================

Câu nói:

"Tưới cây xoài lô B 100 lít nước lúc 6 giờ sáng"

Kết quả mong muốn:

{{
  "activity_text": "Tưới nước",
  "lot_text": "Lô B",
  "materials": [
    {{
      "material_text": "Nước",
      "quantity": 100,
      "unit_text": "lít"
    }}
  ],
  "time_text": "06:00"
}}

========================
VÍ DỤ 3
========================

Câu nói:

"Làm cỏ lô A lúc 8 giờ sáng"

Kết quả mong muốn:

{{
  "activity_text": "Làm cỏ",
  "lot_text": "Lô A",
  "materials": [],
  "time_text": "08:00"
}}

========================
VÍ DỤ 4
========================

Câu nói:

"Thu hoạch xoài lô B lúc 9 giờ"

Kết quả mong muốn:

{{
  "activity_text": "Thu hoạch",
  "lot_text": "Lô B",
  "materials": [],
  "time_text": "09:00"
}}

========================
VÍ DỤ 5
========================

Câu nói:

"Phun thuốc lô C 2 chai thuốc sâu lúc 4 giờ chiều"

Kết quả mong muốn:

{{
  "activity_text": "Phun thuốc",
  "lot_text": "Lô C",
  "materials": [
    {{
      "material_text": "Thuốc sâu",
      "quantity": 2,
      "unit_text": "chai"
    }}
  ],
  "time_text": "16:00"
}}

========================
CÂU NÓI CẦN PHÂN TÍCH
========================

"{transcript}"
"""