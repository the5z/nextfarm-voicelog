# NextFarm VoiceLog — Integration Service

Integration Service là dịch vụ trung gian của hệ thống NextFarm VoiceLog.

Service nhận dữ liệu nhật ký đã được người dùng xác nhận từ Flutter,
kiểm tra dữ liệu nghiệp vụ, chuẩn hóa Master Data, lưu PostgreSQL,
xử lý đồng bộ và chuyển dữ liệu sang định dạng NextFarm.

> Hợp đồng JSON dùng chung giữa AI Service, Flutter và Integration Service
> được mô tả chi tiết tại `../contracts/README.md`.

---

## 1. Vai trò trong hệ thống

Luồng tổng quát:

```text
Speech / AI Service
        ↓
structured_data dạng *_text
        ↓
Flutter
        ↓
Integration Service
        ↓
Master Data Resolve
        ↓
Flutter hiển thị kết quả cho người dùng xác nhận
        ↓
Cultivation Log dạng *_code
        ↓
Integration Service
        ↓
PostgreSQL
        ↓
NextFarm Client
        ↓
Mock / Live
```

Integration Service chịu trách nhiệm:

- Kiểm tra dữ liệu nhật ký.
- Chuẩn hóa Master Data.
- Resolve dữ liệu dạng text sang business code.
- Phát hiện dữ liệu thiếu, không xác định hoặc mơ hồ.
- Lưu nhật ký vào PostgreSQL.
- Lưu nhiều vật tư cho một nhật ký.
- Chống lưu trùng bằng `client_record_id`.
- Xử lý đồng bộ nhiều bản ghi.
- Lấy danh sách và chi tiết nhật ký đã lưu.
- Chuyển Cultivation Log sang payload NextFarm.
- Gửi dữ liệu qua NextFarm Client ở chế độ `mock` hoặc `live`.
- Ghi Integration History cho các thao tác quan trọng.

Integration Service không chịu trách nhiệm:

- Nhận dạng giọng nói.
- Xử lý audio.
- Trích xuất dữ liệu bằng AI.
- Hiển thị giao diện cho người dùng.
- Lưu SQLite trên thiết bị Flutter.

---

## 2. Cấu trúc chính

```text
integration-service/
├── app/
│   ├── clients/
│   ├── data/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── database.py
│   └── main.py
├── migrations/
│   ├── env.py
│   └── versions/
├── tests/
├── .env.example
├── alembic.ini
├── requirements.txt
└── README.md
```

Các nhóm chính:

```text
routers/
→ định nghĩa REST API

schemas/
→ Pydantic request/response model

services/
→ business logic

models/
→ SQLAlchemy database model

data/
→ Master Data hiện dùng trong demo

clients/
→ client tích hợp NextFarm

migrations/
→ Alembic database migration

tests/
→ automated tests
```

---

## 3. Cài đặt

Yêu cầu:

```text
Python 3.12+
PostgreSQL
```

Tạo virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Cài dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

## 4. Cấu hình môi trường

Tạo file:

```text
.env
```

Dựa trên:

```text
.env.example
```

Các cấu hình chính gồm:

```env
DATABASE_URL=postgresql+psycopg://...
DATABASE_ECHO=false

NEXTFARM_MODE=mock
NEXTFARM_BASE_URL=
NEXTFARM_API_TOKEN=
NEXTFARM_PRODUCTION_DIARY_PATH=/api/diary/production
NEXTFARM_TIMEOUT_SECONDS=10
```

Không commit `.env` hoặc token thật lên Git.

---

## 5. Chạy Integration Service

```powershell
python -m uvicorn app.main:app --reload --port 8002
```

Service chạy tại:

```text
http://127.0.0.1:8002
```

Swagger API:

```text
http://127.0.0.1:8002/docs
```

Health check:

```http
GET /health
```

---

## 6. Master Data

Integration Service hiện quản lý bốn nhóm Master Data:

```text
activity
lot
material
unit
```

Ví dụ:

```text
Cho bò ăn → CHO_BO_AN
Lô A       → LO_A
Cám        → CAM
kg         → KG
```

### Resolve một giá trị

```http
POST /api/master-data/resolve
```

Ví dụ:

```json
{
  "data_type": "activity",
  "text": "Cho bò ăn"
}
```

Integration Service hỗ trợ:

```text
exact
alias
fuzzy
ambiguous
none
```

Quy tắc:

```text
exact
→ trả code
→ không cần xác nhận

alias
→ trả code
→ không cần xác nhận

fuzzy
→ chỉ trả code đã tồn tại trong Master Data
→ cần người dùng xác nhận

ambiguous
→ không tự chọn code
→ cần người dùng xác nhận

none
→ không tự tạo code mới
→ cần người dùng xác nhận
```

Các giá trị mơ hồ theo vùng miền như:

```text
xị
công
sào
```

không được tự động quy đổi.

### Resolve toàn bộ dữ liệu canh tác

```http
POST /api/master-data/resolve-cultivation
```

Endpoint này cho phép Flutter gửi một lần:

```json
{
  "activity_text": "Cho bò ăn",
  "lot_text": "Lô A",
  "materials": [
    {
      "material_text": "Cám",
      "quantity": 20,
      "unit_text": "kg"
    }
  ],
  "time_text": "07:00"
}
```

Integration Service trả các business code tương ứng.

`time_text` được giữ nguyên.

Integration Service không tự chuyển `time_text` thành `performed_at`.

---

## 7. Cultivation Log API

### Validate

```http
POST /api/cultivation-logs/validate
```

Kiểm tra dữ liệu trước khi lưu.

### Save

```http
POST /api/cultivation-logs
```

Chỉ nhật ký đã được xác nhận mới được lưu chính thức.

`client_record_id` được dùng để chống duplicate.

Nếu cùng một `client_record_id` được gửi lại, backend trả trạng thái:

```text
already_exists
```

thay vì tạo bản ghi mới.

### List

```http
GET /api/cultivation-logs
```

Trả danh sách nhật ký đã lưu.

### Detail

```http
GET /api/cultivation-logs/{client_record_id}
```

Trả chi tiết một nhật ký cùng danh sách vật tư.

---

## 8. PostgreSQL

Các bảng chính hiện tại:

```text
cultivation_logs
cultivation_log_materials
integration_history
```

Một `cultivation_log` có thể chứa nhiều vật tư trong:

```text
cultivation_log_materials
```

`client_record_id` có unique constraint để bảo vệ chống lưu trùng.

---

## 9. Alembic Migration

Migration được lưu tại:

```text
migrations/versions/
```

Kiểm tra migration hiện tại:

```powershell
python -m alembic current
```

Xem migration head:

```powershell
python -m alembic heads
```

Upgrade database:

```powershell
python -m alembic upgrade head
```

Kiểm tra model và migration có đồng bộ không:

```powershell
python -m alembic check
```

Các migration hiện tại gồm:

```text
0001
→ tạo cultivation_logs và cultivation_log_materials

0002
→ tạo integration_history
```

---

## 10. Offline Sync

Flutter có thể lưu bản ghi offline và gửi lại khi có mạng.

Endpoint:

```http
POST /api/sync/logs
```

Mỗi bản ghi được xử lý độc lập.

Các trạng thái có thể gồm:

```text
saved
already_exists
failed
```

Một bản ghi lỗi không làm toàn bộ batch sync thất bại.

---

## 11. Integration History

Integration Service ghi lại các sự kiện quan trọng để hỗ trợ debug và demo.

Các sự kiện hiện được theo dõi gồm:

```text
save_cultivation_log
submit_nextfarm
```

History lưu:

```text
event_type
client_record_id
request_payload
response_payload
status
http_status
created_at
```

Lấy toàn bộ history:

```http
GET /api/history
```

Lọc theo một nhật ký:

```http
GET /api/history?client_record_id=e2e-voice-001
```

Các thao tác thành công và thất bại đều có thể được ghi lại.

---

## 12. NextFarm Integration

Gửi một nhật ký đã lưu sang NextFarm:

```http
POST /api/nextfarm/cultivation-logs/{client_record_id}/submit
```

### Mock mode

```env
NEXTFARM_MODE=mock
```

Mock mode:

- Không gọi API NextFarm thật.
- Không cần token.
- Dùng cho development, automated test và demo.
- Trả kết quả mô phỏng `accepted`.

Ví dụ:

```text
mode = mock
status = accepted
status_code = 200
```

### Live mode

```env
NEXTFARM_MODE=live
```

Live mode chỉ nên sử dụng khi có:

- URL API NextFarm chính thức.
- Token hợp lệ.
- Endpoint chính thức.
- Tài liệu mapping chính thức.
- Môi trường tích hợp được cấp phép.

Payload NextFarm hiện tại là payload mô phỏng cho đồ án và không được mô tả là contract chính thức của NextFarm.

Chi tiết xem:

```text
../contracts/README.md
```

---

## 13. Automated Tests

Chạy toàn bộ test:

```powershell
python -m pytest -q
```

Có thể chạy riêng từng nhóm:

```powershell
python -m pytest .\tests\test_master_data.py -q
python -m pytest .\tests\test_cultivation_logs.py -q
python -m pytest .\tests\test_history.py -q
python -m pytest .\tests\test_sync.py -q
python -m pytest .\tests\test_nextfarm_api.py -q
```

Trước khi commit nên kiểm tra:

```powershell
python -m pytest -q
python -m alembic check
git diff --check
```

---

## 14. Luồng demo Integration

Ví dụ luồng:

```text
AI trả:
activity_text = "Cho bò ăn"
lot_text = "Lô A"
material_text = "Cám"
quantity = 20
unit_text = "kg"
time_text = "07:00"

        ↓

POST /api/master-data/resolve-cultivation

        ↓

activity_code = CHO_BO_AN
lot_code = LO_A
material_code = CAM
unit_code = KG

        ↓

Người dùng xác nhận trên Flutter

        ↓

POST /api/cultivation-logs/validate

        ↓

POST /api/cultivation-logs

        ↓

PostgreSQL

        ↓

GET /api/cultivation-logs/{client_record_id}

        ↓

POST /api/nextfarm/cultivation-logs/{client_record_id}/submit

        ↓

NextFarm mock accepted

        ↓

GET /api/history?client_record_id={client_record_id}
```

---

## 15. Contracts

Integration Service sử dụng contract chung tại:

```text
../contracts/
```

Tài liệu đầy đủ:

```text
../contracts/README.md
```

Không tự ý thay đổi:

```text
field name
data type
schema version
business code contract
```

mà chưa thống nhất với AI Service và Flutter.