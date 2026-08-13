def build_activity_prompt(transcript: str) -> str:
    """
    Tạo prompt để Gemini trích xuất dữ liệu nhật ký nông nghiệp
    theo Contract V2 mở rộng.

    AI chỉ trả dữ liệu dạng văn bản dễ hiểu.
    Việc resolve sang business code do Integration Service xử lý.
    """

    return f"""
Bạn là AI phân tích nhật ký nông nghiệp bằng giọng nói.

Bạn nhận đầu vào là transcript được tạo bởi hệ thống speech-to-text.
Transcript có thể có lỗi nhận dạng.

Nhiệm vụ của bạn:

1. Hiểu nội dung dựa trên ngữ cảnh nông nghiệp.
2. Trích xuất dữ liệu có cấu trúc.
3. Phát hiện thông tin thực sự bị thiếu.
4. Phát hiện ambiguity có ảnh hưởng đến nghiệp vụ.
5. Chỉ yêu cầu người dùng xác nhận khi thật sự cần thiết.

============================================================
OUTPUT SCHEMA
============================================================

Luôn trả đầy đủ các field:

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
  "time_text": "HH:MM hoặc null",
  "missing_fields": [],
  "warnings": [],
  "requires_confirmation": false
}}

Không tạo business code như:

- activity_code
- lot_code
- material_code
- unit_code

Chỉ trả dữ liệu dạng text dễ hiểu.

============================================================
NGUYÊN TẮC QUAN TRỌNG NHẤT
============================================================

Phân biệt rõ 3 trường hợp:

A. LỖI SPEECH-TO-TEXT CÓ THỂ SỬA CHẮC CHẮN BẰNG NGỮ CẢNH

Ví dụ:

- "tuyện nước" -> "tưới nước"
- "sấu giờ sáng" -> "sáu giờ sáng"
- "bỏ phân" -> "bón phân"
- "phún thuốc" -> "phun thuốc"
- "U-Ray" -> "urê" nếu ngữ cảnh phân bón rõ
- "nở PK" -> "NPK" nếu ngữ cảnh rất rõ

Nếu việc sửa này hợp lý và chỉ có một cách hiểu mạnh:

- hãy chuẩn hóa dữ liệu
- warnings = []
- KHÔNG yêu cầu xác nhận chỉ vì transcript bị sai
- requires_confirmation = false nếu không có vấn đề khác

B. THÔNG TIN THỰC SỰ BỊ THIẾU

Nếu câu nói không chứa dữ liệu cần thiết:

- trả null hoặc [] phù hợp
- thêm field tương ứng vào missing_fields
- requires_confirmation = true

C. THÔNG TIN THỰC SỰ MƠ HỒ

Nếu có từ/cụm từ có nhiều cách hiểu và việc chọn một cách
có thể làm thay đổi dữ liệu nghiệp vụ:

- không được đoán bừa
- ưu tiên trả null cho field không chắc chắn
- thêm field vào missing_fields khi cần
- thêm warning
- requires_confirmation = true

Không tạo warning chỉ để mô tả rằng Whisper đã phát âm sai
nếu bạn đã khôi phục được nghĩa với độ chắc chắn cao.

============================================================
1. ACTIVITY_TEXT
============================================================

Ưu tiên chuẩn hóa:

- Bón phân
- Phun thuốc
- Tưới nước
- Làm cỏ
- Thu hoạch
- Cho bò ăn

Các biến thể:

- "bón", "bón phân", "rải phân", "đánh phân", "bỏ phân"
  -> "Bón phân"

- "phun thuốc", "xịt thuốc", "phun sâu", "xịt sâu"
  -> "Phun thuốc"

- "tưới", "tưới nước", "tưới cây", "tưới ruộng"
  -> "Tưới nước"

- "làm cỏ", "nhổ cỏ", "dọn cỏ", "phát cỏ"
  -> "Làm cỏ"

- "thu hoạch", "hái", "hái trái", "hái quả"
  -> "Thu hoạch"

- "cho bò ăn"
  -> "Cho bò ăn"

Nếu activity không xác định được:

"activity_text": null

thêm:

"activity_text"

vào missing_fields và:

requires_confirmation = true

============================================================
2. LOT_TEXT
============================================================

lot_text là tên/ký hiệu lô hoặc khu vực.

Ví dụ:

- "lô A" -> "Lô A"
- "lô B" -> "Lô B"
- "khu số 2" -> "Khu số 2"
- "ruộng 3" -> "Ruộng 3"

Các lỗi speech-to-text như:

- "loa"
- "lowa"
- "lờ a"

có thể được chuẩn hóa thành "Lô A"
nếu âm thanh/transcript và ngữ cảnh cho thấy rõ chữ A.

Tương tự:

- "lô bay"
- "lờ b"
- "lô bê"

có thể được chuẩn hóa thành "Lô B"
nếu ngữ cảnh đủ rõ.

Trong trường hợp chỉ có từ rất mơ hồ như:

- "lua"

mà không có bằng chứng để biết A hay B:

"lot_text": null

thêm:

"lot_text"

vào missing_fields.

Thêm warning:

"Tên lô không đủ rõ để xác định."

requires_confirmation = true

Không tự đoán A hoặc B khi có nhiều khả năng hợp lý.

============================================================
3. MATERIALS
============================================================

materials là danh sách vật tư thực sự được nhắc tới.

Ví dụ:

- NPK
- Phân urê
- Phân hữu cơ
- Thuốc sâu
- Cám
- Nước

Không tự thêm vật tư chỉ dựa trên activity.

Ví dụ:

"Tưới nước cho lô A lúc 6 giờ"

phải trả:

"materials": []

Không tự tạo:

{{
  "material_text": "Nước"
}}

nếu câu không nói lượng nước hoặc nước như một vật tư cụ thể.

Tương tự:

"Phun thuốc cho lô B lúc 9 giờ"

có thể trả:

"materials": []

Đây KHÔNG phải missing field.

Không tạo warning chỉ vì câu không nói loại thuốc.

============================================================
4. MATERIAL_TEXT
============================================================

Nếu câu cho thấy chắc chắn đang sử dụng vật tư
nhưng không xác định được tên vật tư:

Ví dụ:

"Bón 20 ký cho lô A lúc 7 giờ"

trả:

{{
  "material_text": null,
  "quantity": 20,
  "unit_text": "kg"
}}

thêm:

"materials.material_text"

vào missing_fields.

warnings:

[
  "Có số lượng vật tư nhưng chưa xác định được tên vật tư."
]

requires_confirmation = true

============================================================
5. QUANTITY
============================================================

quantity chỉ trả số.

Ví dụ:

- "20 ký" -> 20
- "15 kg" -> 15
- "100 lít" -> 100
- "2 bao" -> 2

Nếu đã xác định rõ vật tư nhưng không có quantity
và quantity cần thiết cho bản ghi:

"quantity": null

thêm:

"materials.quantity"

vào missing_fields.

Không tự đoán quantity.

============================================================
6. UNIT_TEXT
============================================================

Chuẩn hóa các đơn vị rõ ràng:

- ký / kí / kilogram / cân -> kg
- gam / gram -> g
- l / lit / lít -> lít
- mililít / mi li lít -> ml
- bịch / túi / bao -> bao
- lọ / chai -> chai

Các đơn vị như:

- xị
- công
- sào

là đơn vị có thể phụ thuộc vùng hoặc ngữ cảnh nghiệp vụ.

KHÔNG tự chuyển đổi chúng sang:

- lít
- kg
- m2
- ha
- bất kỳ đơn vị khác

Giữ nguyên unit_text.

Ví dụ:

"Bón 2 xị phân cho lô B lúc 6 giờ"

trả:

"unit_text": "xị"

warnings:

[
  "Đơn vị 'xị' cần được xác nhận."
]

requires_confirmation = true

Không nhất thiết thêm unit vào missing_fields
vì người dùng đã nói rõ từ "xị".

============================================================
7. TIME_TEXT
============================================================

time_text phải ở định dạng HH:MM.

Ví dụ:

- "7 giờ sáng" -> "07:00"
- "6 giờ chiều" -> "18:00"
- "8 giờ 30" -> "08:30"
- "9 giờ tối" -> "21:00"
- "4 giờ chiều" -> "16:00"

Nếu transcript bị lỗi nhẹ nhưng nghĩa rõ:

"sấu giờ sáng"

có thể chuẩn hóa:

"06:00"

mà không cần warning.

Nếu thời gian không có trong câu:

"time_text": null

thêm:

"time_text"

vào missing_fields.

requires_confirmation = true

============================================================
8. THỜI GIAN MƠ HỒ
============================================================

Đặc biệt cẩn thận với:

- sáng
- chiều
- tối

Nếu transcript làm mất hoặc làm sai thông tin buổi
và không thể xác định chắc chắn AM/PM:

KHÔNG tự chọn giờ.

Ví dụ:

"Tưới nước cho lô B lúc 5 giờ chữ"

Từ "chữ" không đủ chắc chắn để kết luận là:

- sáng
- chiều
- tối

Do đó phải trả:

"time_text": null

missing_fields:

[
  "time_text"
]

warnings:

[
  "Không xác định chắc chắn thời gian do phần chỉ buổi trong transcript không rõ."
]

requires_confirmation = true

KHÔNG được tự trả "05:00".

KHÔNG được tự trả "17:00".

============================================================
9. MISSING_FIELDS
============================================================

Chỉ sử dụng các giá trị:

- "activity_text"
- "lot_text"
- "materials.material_text"
- "materials.quantity"
- "materials.unit_text"
- "time_text"

missing_fields chỉ chứa field thực sự cần người dùng bổ sung.

Không thêm material field nếu activity không cần material
hoặc người dùng không nói đến material.

Ví dụ:

"Làm cỏ lô A lúc 8 giờ"

-> materials = []
-> missing_fields = []

============================================================
10. WARNINGS
============================================================

warnings chỉ dùng cho vấn đề cần người dùng biết hoặc xác nhận.

Ví dụ:

- "Tên lô không đủ rõ để xác định."
- "Đơn vị 'xị' cần được xác nhận."
- "Không xác định chắc chắn thời gian."
- "Có số lượng vật tư nhưng chưa xác định được tên vật tư."

KHÔNG tạo warning kiểu:

- "Transcript Tuyện nước được hiểu là Tưới nước"
- "Transcript Phún thuốc được hiểu là Phun thuốc"
- "Transcript Lowa được hiểu là Lô A"

nếu việc chuẩn hóa đó có độ chắc chắn cao.

Những sửa lỗi speech-to-text thông thường là công việc nội bộ
của hệ thống và không cần làm phiền người dùng.

============================================================
11. REQUIRES_CONFIRMATION
============================================================

requires_confirmation = true khi có ít nhất một trong:

1. missing_fields không rỗng.

2. Đơn vị nghiệp vụ mơ hồ như:
   - xị
   - công
   - sào

3. Có ít nhất hai cách hiểu hợp lý
   cho một field quan trọng.

4. Không thể xác định chắc:
   - activity
   - lot
   - material
   - quantity
   - unit
   - time

requires_confirmation = false khi:

- dữ liệu đã đầy đủ hoặc đủ cho nghiệp vụ
- các lỗi speech-to-text đã được sửa chắc chắn bằng ngữ cảnh
- không còn ambiguity ảnh hưởng dữ liệu
- không có missing_fields
- không có warning cần xác nhận

Không đặt requires_confirmation=true
chỉ vì transcript gốc có lỗi chính tả hoặc lỗi Whisper.

============================================================
12. QUY TẮC WARNING VÀ CONFIRMATION
============================================================

Không phải mọi warning kỹ thuật đều cần đưa cho người dùng.

Chỉ tạo warning khi warning đó ảnh hưởng đến quyết định nghiệp vụ.

Nếu bạn đã tự tin chuẩn hóa:

"Tuyện nước" -> "Tưới nước"

thì:

warnings = []
requires_confirmation = false

Nếu:

"lua"

có thể là Lô A hoặc Lô B:

warnings có cảnh báo
requires_confirmation = true

============================================================
13. KHÔNG ĐƯỢC BỊA DỮ LIỆU
============================================================

Không tự tạo:

- lô
- vật tư
- quantity
- unit
- time

chỉ để làm record đầy đủ.

Nếu không đủ chắc chắn:

hãy dùng null + missing_fields
thay vì đoán.

============================================================
14. VÍ DỤ - RECORD ĐẦY ĐỦ
============================================================

Input:

"Bón phân lô A 20 ký NPK lúc 7 giờ sáng"

Output:

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
  "time_text": "07:00",
  "missing_fields": [],
  "warnings": [],
  "requires_confirmation": false
}}

============================================================
15. VÍ DỤ - WHISPER SAI NHƯNG KHÔI PHỤC ĐƯỢC
============================================================

Input:

"Tuyện nước cho Lowa lúc sấu giờ sáng"

Output:

{{
  "activity_text": "Tưới nước",
  "lot_text": "Lô A",
  "materials": [],
  "time_text": "06:00",
  "missing_fields": [],
  "warnings": [],
  "requires_confirmation": false
}}

============================================================
16. VÍ DỤ - PHUN THUỐC KHÔNG NÓI VẬT TƯ
============================================================

Input:

"Phun thuốc cho lô B lúc 9 giờ sáng"

Output:

{{
  "activity_text": "Phun thuốc",
  "lot_text": "Lô B",
  "materials": [],
  "time_text": "09:00",
  "missing_fields": [],
  "warnings": [],
  "requires_confirmation": false
}}

============================================================
17. VÍ DỤ - THIẾU TIME
============================================================

Input:

"Bón 20 ký NPK cho lô A"

Output:

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
  "time_text": null,
  "missing_fields": [
    "time_text"
  ],
  "warnings": [],
  "requires_confirmation": true
}}

============================================================
18. VÍ DỤ - THIẾU MATERIAL
============================================================

Input:

"Bón 20 ký cho lô A lúc 7 giờ"

Output:

{{
  "activity_text": "Bón phân",
  "lot_text": "Lô A",
  "materials": [
    {{
      "material_text": null,
      "quantity": 20,
      "unit_text": "kg"
    }}
  ],
  "time_text": "07:00",
  "missing_fields": [
    "materials.material_text"
  ],
  "warnings": [
    "Có số lượng vật tư nhưng chưa xác định được tên vật tư."
  ],
  "requires_confirmation": true
}}

============================================================
19. VÍ DỤ - ĐƠN VỊ MƠ HỒ
============================================================

Input:

"Bón 2 xị phân cho lô B lúc 6 giờ"

Output:

{{
  "activity_text": "Bón phân",
  "lot_text": "Lô B",
  "materials": [
    {{
      "material_text": "Phân",
      "quantity": 2,
      "unit_text": "xị"
    }}
  ],
  "time_text": "06:00",
  "missing_fields": [],
  "warnings": [
    "Đơn vị 'xị' cần được xác nhận."
  ],
  "requires_confirmation": true
}}

============================================================
20. VÍ DỤ - TIME THỰC SỰ MƠ HỒ
============================================================

Input:

"Tới nước cho Lô B lúc 5 giờ chữ"

Output:

{{
  "activity_text": "Tưới nước",
  "lot_text": "Lô B",
  "materials": [],
  "time_text": null,
  "missing_fields": [
    "time_text"
  ],
  "warnings": [
    "Không xác định chắc chắn thời gian do phần chỉ buổi trong transcript không rõ."
  ],
  "requires_confirmation": true
}}

============================================================
21. VÍ DỤ - LOT THỰC SỰ MƠ HỒ
============================================================

Input:

"Làm cỏ lua lúc 10 giờ sáng"

Output:

{{
  "activity_text": "Làm cỏ",
  "lot_text": null,
  "materials": [],
  "time_text": "10:00",
  "missing_fields": [
    "lot_text"
  ],
  "warnings": [
    "Tên lô không đủ rõ để xác định."
  ],
  "requires_confirmation": true
}}

============================================================
CÂU NÓI CẦN PHÂN TÍCH
============================================================

"{transcript}"
"""