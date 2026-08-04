# NextFarm VoiceLog — JSON Integration Contracts

Thư mục này chứa các hợp đồng JSON dùng để tích hợp ba thành phần của hệ thống NextFarm VoiceLog:

1. Speech/AI Service.
2. Flutter Mobile Application.
3. Integration Service.

Các hợp đồng trong thư mục này là nguồn tham chiếu chung về:

- Tên trường JSON.
- Kiểu dữ liệu.
- Trường bắt buộc.
- Giá trị hợp lệ.
- Cách xử lý dữ liệu thiếu.
- Cách đồng bộ dữ liệu offline.
- Payload mô phỏng gửi sang NextFarm.

Không thành viên nào được tự ý đổi tên trường hoặc thay đổi kiểu dữ liệu mà chưa thống nhất với các thành viên còn lại.

---

## 1. Cấu trúc thư mục

```text
contracts/
├── README.md
├── ai-extraction-response.schema.json
├── cultivation-log.schema.json
├── nextfarm-payload.schema.json
├── cultivation-log.example.json
├── validation-response.example.json
├── save-response.example.json
├── sync-request.example.json
├── sync-response.example.json
├── nextfarm-production-diary.example.json
└── examples/
    ├── ai-extraction-response.json
    ├── ai-extraction-missing-fields.json
    ├── cultivation-log-valid.json
    └── nextfarm-payload.json
```

### Các file schema chính

| File | Mục đích |
|---|---|
| `ai-extraction-response.schema.json` | Dữ liệu Speech/AI Service trả về sau khi nhận dạng và trích xuất |
| `cultivation-log.schema.json` | Nhật ký Flutter gửi tới Integration Service |
| `nextfarm-payload.schema.json` | Payload mô phỏng Integration Service chuyển sang NextFarm |

### Các file ví dụ chuẩn

| File | Mục đích |
|---|---|
| `examples/ai-extraction-response.json` | Kết quả AI đầy đủ |
| `examples/ai-extraction-missing-fields.json` | Kết quả AI còn thiếu dữ liệu |
| `examples/cultivation-log-valid.json` | Nhật ký hợp lệ Flutter gửi lên backend |
| `examples/nextfarm-payload.json` | Payload NextFarm mock sau khi chuyển đổi |

Các file ví dụ nằm trực tiếp trong thư mục `contracts/` được giữ lại để tương thích với các đường dẫn cũ của dự án.

Khi phát triển chức năng mới, ưu tiên dùng các file trong thư mục `contracts/examples/`.

---

## 2. Luồng tích hợp tổng thể

```text
Người dùng nói
    ↓
Speech/AI Service nhận dạng giọng nói
    ↓
AI trả ai-extraction-response
    ↓
Flutter hiển thị transcript và dữ liệu đã trích xuất
    ↓
Người dùng kiểm tra, sửa và xác nhận
    ↓
Flutter tạo cultivation-log
    ↓
Integration Service validate dữ liệu
    ↓
Integration Service lưu PostgreSQL
    ↓
Nếu thiết bị offline, Flutter lưu SQLite và đồng bộ lại sau
    ↓
Integration Service chuyển nhật ký thành nextfarm-payload
    ↓
NextFarm Client gửi ở chế độ mock hoặc live
```

---

## 3. Phân chia trách nhiệm

### 3.1. Speech/AI Service — Thắng

Speech/AI Service chịu trách nhiệm:

- Nhận file âm thanh hoặc dữ liệu ghi âm.
- Chuyển giọng nói tiếng Việt thành transcript.
- Trích xuất hoạt động canh tác.
- Trích xuất mã lô.
- Trích xuất vật tư.
- Trích xuất số lượng và đơn vị.
- Trích xuất thời điểm thực hiện.
- Phát hiện trường chưa xác định.
- Trả cảnh báo khi đơn vị hoặc nội dung mơ hồ.
- Trả kết quả theo schema `contracts/ai-extraction-response.schema.json`.

Ví dụ đầy đủ:

```text
contracts/examples/ai-extraction-response.json
```

Ví dụ thiếu dữ liệu:

```text
contracts/examples/ai-extraction-missing-fields.json
```

Speech/AI Service không chịu trách nhiệm tạo:

- `client_record_id` của nhật ký lưu trên thiết bị.
- Trạng thái `confirmed`.
- Trạng thái đồng bộ SQLite.
- ID trong PostgreSQL.
- Payload NextFarm.

Khi mô hình không có độ tin cậy đáng tin cậy, các trường trong `confidence` phải trả về `null`, không được tự đặt số ngẫu nhiên.

### 3.2. Flutter Application — Khoa

Flutter chịu trách nhiệm:

- Gửi âm thanh tới Speech/AI Service.
- Nhận kết quả AI.
- Hiển thị transcript.
- Hiển thị các trường AI đã trích xuất.
- Hiển thị `missing_fields` và `warnings`.
- Cho người dùng sửa dữ liệu.
- Cho người dùng xác nhận dữ liệu.
- Tạo `client_record_id`.
- Giữ nguyên `client_record_id` trong toàn bộ vòng đời bản ghi.
- Gửi dữ liệu đến Integration Service.
- Lưu bản ghi vào SQLite khi thiết bị offline.
- Đồng bộ lại khi có mạng.
- Cập nhật trạng thái bản ghi theo kết quả sync.

Flutter gửi nhật ký theo schema:

```text
contracts/cultivation-log.schema.json
```

Ví dụ:

```text
contracts/examples/cultivation-log-valid.json
```

#### Quy tắc đối với `client_record_id`

`client_record_id` phải:

- Được tạo trên thiết bị.
- Là duy nhất.
- Không thay đổi khi gửi lại.
- Không thay đổi khi retry.
- Không thay đổi khi đồng bộ offline.
- Không tạo ID mới sau mỗi lần gửi thất bại.

Ví dụ:

```text
android-device-001-record-0001
```

Integration Service dùng trường này để chống lưu trùng.

#### Quy tắc đối với `confirmed`

Trước khi người dùng xác nhận:

```json
{
  "confirmed": false
}
```

Sau khi người dùng kiểm tra và xác nhận:

```json
{
  "confirmed": true
}
```

Bản ghi chưa xác nhận có thể được gọi API kiểm tra dữ liệu, nhưng không nên được coi là nhật ký hoàn chỉnh để lưu chính thức.

### 3.3. Integration Service — Hiệp

Integration Service chịu trách nhiệm:

- Nhận JSON từ Flutter.
- Kiểm tra schema và dữ liệu nghiệp vụ.
- Chuẩn hóa mã hoạt động, mã lô, mã vật tư và đơn vị.
- Phát hiện dữ liệu thiếu hoặc không hợp lệ.
- Lưu nhật ký vào PostgreSQL.
- Lưu nhiều vật tư cho một nhật ký.
- Chống trùng bằng `client_record_id`.
- Xử lý đồng bộ nhiều bản ghi.
- Trả kết quả riêng cho từng bản ghi sync.
- Chuyển dữ liệu sang payload NextFarm mock.
- Gửi payload qua NextFarm Client.
- Hỗ trợ hai chế độ `mock` và `live`.

Integration Service không chịu trách nhiệm:

- Nhận dạng âm thanh.
- Trích xuất dữ liệu bằng AI.
- Hiển thị giao diện chỉnh sửa.
- Lưu SQLite trên điện thoại.

---

## 4. Quy tắc chung của hợp đồng JSON

### 4.1. Phiên bản schema

Phiên bản hiện tại:

```json
{
  "schema_version": "1.0"
}
```

Không tự ý thay đổi thành:

```json
{
  "schemaVersion": "1.0"
}
```

hoặc:

```json
{
  "version": "1.0"
}
```

Mọi thay đổi không tương thích phải tăng phiên bản hợp đồng.

Ví dụ:

```json
{
  "schema_version": "2.0"
}
```

### 4.2. Quy tắc đặt tên trường

JSON sử dụng `snake_case`.

Đúng:

```text
client_record_id
activity_code
lot_code
performed_at
performer_code
material_code
unit_code
```
Lưu ý về hai giai đoạn dữ liệu:

- Kết quả từ Speech/AI Service gửi Flutter sử dụng các trường dữ liệu thô:
  `activity_text`, `lot_text`, `material_text`, `unit_text`.
- Sau khi Flutter gọi Integration Service để resolve và người dùng xác nhận,
  JSON cuối gửi backend sử dụng:
  `activity_code`, `lot_code`, `material_code`, `unit_code`.
Không dùng:

```text
clientRecordId
activityCode
lotCode
performedAt
performerCode
```

Flutter có thể dùng camelCase trong class Dart nội bộ, nhưng khi serialize JSON gửi backend phải chuyển đúng về `snake_case`.

### 4.3. Thời gian

Các trường thời gian phải dùng ISO 8601 và nên có múi giờ.

Ví dụ đúng:

```text
2026-08-03T07:00:00+07:00
```

Ví dụ UTC:

```text
2026-08-03T00:00:00Z
```

Không gửi các dạng mơ hồ:

```text
07:00 sáng nay
03/08/2026 07:00
7 giờ
```

AI có thể trả `performed_at: null` khi chưa xác định được thời gian. Flutter phải yêu cầu người dùng bổ sung trước khi lưu chính thức.

### 4.4. Mã hoạt động

Các mã hoạt động hiện được hỗ trợ:

```text
BON_PHAN
PHUN_THUOC
TUOI_NUOC
LAM_CO
THU_HOACH
```

Mã phải viết hoa và dùng dấu gạch dưới.

Ví dụ:

```json
{
  "activity_code": "BON_PHAN"
}
```

### 4.5. Đơn vị

Các đơn vị Integration Service hiện hỗ trợ:

```text
KG
G
L
ML
BAG
BOTTLE
```

| Mã | Ý nghĩa |
|---|---|
| `KG` | Kilogram |
| `G` | Gram |
| `L` | Lít |
| `ML` | Mililít |
| `BAG` | Bao |
| `BOTTLE` | Chai |

Không tự động quy đổi các đơn vị địa phương hoặc mơ hồ như:

```text
xị
công
sào
```

Khi gặp đơn vị mơ hồ, Speech/AI Service phải:

1. Để `unit_text` bằng `null`.
2. Thêm `materials.unit_text` vào `missing_fields`.
3. Flutter hiển thị cảnh báo và yêu cầu người dùng chọn đơn vị chuẩn.
4. Sau khi xác nhận, Flutter gọi API resolve để lấy `unit_code`.

### 4.6. Số lượng vật tư

`quantity` phải lớn hơn `0`.

Ví dụ hợp lệ:

```json
{
  "quantity": 20
}
```

```json
{
  "quantity": 2.5
}
```

Không hợp lệ:

```json
{
  "quantity": 0
}
```

```json
{
  "quantity": -5
}
```

Trong kết quả AI, `quantity` được phép là `null` khi chưa nhận dạng được. Trong nhật ký Flutter gửi để lưu, `quantity` phải là số dương.

---


## 5. Hợp đồng Speech/AI Response

Schema:

```text
contracts/ai-extraction-response.schema.json
```

File ví dụ:

```text
contracts/examples/ai-extraction-response.json
contracts/examples/ai-extraction-missing-fields.json
```

### 5.1. Trách nhiệm của Speech/AI Service

Speech/AI Service thực hiện:

1. Chuyển âm thanh thành transcript tiếng Việt.
2. Trích xuất tên hoạt động, lô, vật tư, số lượng, đơn vị và thời gian.
3. Giữ dữ liệu nghiệp vụ ở dạng văn bản dễ hiểu.
4. Phát hiện trường còn thiếu hoặc chưa chắc chắn.
5. Trả về cảnh báo và độ tin cậy nếu mô hình có hỗ trợ.

Speech/AI Service không tự suy đoán các mã:

```text
activity_code
lot_code
material_code
unit_code
performer_code
```

Việc ánh xạ tên sang mã được thực hiện thông qua Master Data API của Integration Service.

### 5.2. Cấu trúc response

```json
{
  "schema_version": "1.0",
  "request_id": "speech-request-0001",
  "transcript": "Ngày 3 tháng 8 năm 2026, bón 20 kg phân NPK cho lô A1 lúc 7 giờ sáng",
  "activity_text": "Bón phân",
  "lot_text": "Lô A1",
  "materials": [
    {
      "material_text": "Phân NPK",
      "quantity": 20,
      "unit_text": "kg"
    }
  ],
  "time_text": "7 giờ sáng ngày 03/08/2026",
  "performed_at": "2026-08-03T07:00:00+07:00",
  "notes": null,
  "missing_fields": [],
  "warnings": [],
  "confidence": {
    "overall": 0.93,
    "transcript": 0.97,
    "activity_text": 0.95,
    "lot_text": 0.91,
    "materials": 0.94,
    "performed_at": 0.88
  }
}
```

### 5.3. Ý nghĩa các trường chính

| Trường | Ý nghĩa |
|---|---|
| `schema_version` | Phiên bản hợp đồng dữ liệu |
| `request_id` | Mã đối chiếu request và response |
| `transcript` | Toàn bộ văn bản nhận dạng từ âm thanh |
| `activity_text` | Tên hoạt động dạng văn bản |
| `lot_text` | Tên lô hoặc khu vực dạng văn bản |
| `materials` | Danh sách vật tư AI trích xuất |
| `material_text` | Tên vật tư dạng văn bản |
| `quantity` | Số lượng vật tư |
| `unit_text` | Đơn vị nguyên bản từ lời nói |
| `time_text` | Cụm từ thời gian nguyên bản |
| `performed_at` | Thời điểm ISO 8601 nếu xác định chính xác |
| `notes` | Thông tin bổ sung |
| `missing_fields` | Danh sách trường còn thiếu |
| `warnings` | Cảnh báo cho Flutter hiển thị |
| `confidence` | Độ tin cậy từ 0 đến 1 hoặc `null` |

### 5.4. Trường hợp còn thiếu dữ liệu

```json
{
  "schema_version": "1.0",
  "request_id": "speech-request-0002",
  "transcript": "Sáng nay bón phân cho lô A1",
  "activity_text": "Bón phân",
  "lot_text": "Lô A1",
  "materials": [
    {
      "material_text": null,
      "quantity": null,
      "unit_text": null
    }
  ],
  "time_text": "Sáng nay",
  "performed_at": null,
  "notes": null,
  "missing_fields": [
    "performed_at",
    "materials.material_text",
    "materials.quantity",
    "materials.unit_text"
  ],
  "warnings": [
    {
      "field": "materials",
      "code": "INCOMPLETE_MATERIAL",
      "message": "Chưa xác định được tên vật tư, số lượng và đơn vị."
    },
    {
      "field": "performed_at",
      "code": "MISSING_PERFORMED_AT",
      "message": "Chưa xác định được ngày giờ thực hiện chính xác."
    }
  ],
  "confidence": {
    "overall": 0.62,
    "transcript": 0.94,
    "activity_text": 0.9,
    "lot_text": 0.88,
    "materials": 0.35,
    "performed_at": null
  }
}
```

Flutter phải hiển thị các trường thiếu và cảnh báo để người dùng bổ sung trước khi xác nhận.

### 5.5. Luồng ánh xạ sang mã

```text
Speech/AI Service
→ trả activity_text, lot_text, material_text, unit_text
→ Flutter hiển thị dữ liệu
→ Flutter gọi POST /api/master-data/resolve
→ Integration Service trả code tương ứng
→ người dùng kiểm tra và xác nhận
→ Flutter gửi Cultivation Log có các trường *_code
```

Master Data API hiện hỗ trợ:

```text
activity
unit
lot
material
```

Ví dụ resolve:

```json
{
  "data_type": "material",
  "text": "Cám"
}
```

Response:

```json
{
  "matched": true,
  "code": "CAM",
  "name": "Cám",
  "confidence": 1.0,
  "requires_confirmation": false,
  "normalized_text": "cám",
  "message": "Đã chuẩn hóa chính xác."
}
```

Nếu không tìm thấy hoặc chỉ khớp gần đúng, Flutter phải yêu cầu người dùng xác nhận; không tự động gửi mã chưa chắc chắn vào Cultivation Log.
## 6. Hợp đồng Cultivation Log

Schema:

```text
contracts/cultivation-log.schema.json
```

Ví dụ:

```text
contracts/examples/cultivation-log-valid.json
```

Cấu trúc:

```json
{
  "schema_version": "1.0",
  "client_record_id": "android-device-001-record-0001",
  "transcript": "Bón 20 kg phân NPK cho lô A1 lúc 7 giờ sáng",
  "lot_code": "LO_A1",
  "activity_code": "BON_PHAN",
  "materials": [
    {
      "material_code": "NPK",
      "quantity": 20,
      "unit_code": "KG"
    }
  ],
  "performed_at": "2026-08-03T07:00:00+07:00",
  "performer_code": "NV001",
  "notes": null,
  "source": "voice",
  "confirmed": true
}
```

### Các trường bắt buộc

```text
schema_version
client_record_id
lot_code
activity_code
materials
performed_at
source
confirmed
```

### Các trường có thể là null

```text
transcript
performer_code
notes
```

`materials` có thể là mảng rỗng đối với hoạt động không sử dụng vật tư.

---

## 7. API Integration Service

Địa chỉ khi chạy local:

```text
http://127.0.0.1:8002
```

Swagger:

```text
http://127.0.0.1:8002/docs
```

### Kiểm tra hệ thống

```http
GET /health
```

### Kiểm tra dữ liệu trước khi lưu

```http
POST /api/cultivation-logs/validate
```

Body dùng cấu trúc của:

```text
contracts/cultivation-log.schema.json
```

### Lưu nhật ký

```http
POST /api/cultivation-logs
```

### Lấy danh sách nhật ký

```http
GET /api/cultivation-logs
```

### Lấy danh mục hoạt động

```http
GET /api/master-data/activities
```

### Lấy danh mục đơn vị

```http
GET /api/master-data/units
```

### Chuẩn hóa dữ liệu

```http
POST /api/master-data/resolve
```

### Đồng bộ bản ghi offline

```http
POST /api/sync/logs
```

### Kiểm tra router NextFarm

```http
GET /api/nextfarm/test
```

### Gửi nhật ký đã lưu sang NextFarm

```http
POST /api/nextfarm/cultivation-logs/{client_record_id}/submit
```

---

## 8. Quy tắc đồng bộ offline

Flutter lưu bản ghi chưa đồng bộ trong SQLite.

Mỗi bản ghi phải có:

- `client_record_id`.
- Payload nhật ký.
- Trạng thái local.
- Số lần retry nếu cần.
- Thời điểm tạo.
- Thời điểm cập nhật.

Khi có mạng, Flutter gửi các bản ghi qua:

```http
POST /api/sync/logs
```

Các trạng thái phản hồi có thể gồm:

```text
saved
already_exists
failed
```

Flutter xử lý như sau:

| Trạng thái backend | Xử lý trên Flutter |
|---|---|
| `saved` | Đánh dấu đã đồng bộ |
| `already_exists` | Đánh dấu đã đồng bộ, không gửi lại |
| `failed` | Giữ lại để người dùng sửa hoặc retry |

Một bản ghi lỗi không được làm toàn bộ danh sách sync thất bại.

---

## 9. Payload NextFarm mock

Schema:

```text
contracts/nextfarm-payload.schema.json
```

Ví dụ:

```text
contracts/examples/nextfarm-payload.json
```

Integration Service chuyển nhật ký nội bộ thành payload có dạng:

```json
{
  "name": "Bón phân",
  "start": "2026-08-03T07:00:00+07:00",
  "end": "2026-08-03T07:00:00+07:00",
  "description": "Nội dung nhật ký và vật tư",
  "images": [],
  "location": "LO_A1",
  "assigned_to": "NV001",
  "category_task_id": "BON_PHAN",
  "season_id": "LO_A1",
  "metadata": {
    "schema_version": "1.0",
    "client_record_id": "android-device-001-record-0001",
    "source": "voice",
    "integration_source": "nextfarm-voicelog"
  }
}
```

### Cảnh báo quan trọng

Payload này là định dạng mô phỏng phục vụ đồ án.

Hiện tại chưa khẳng định:

- Endpoint NextFarm chính thức.
- Tên trường NextFarm chính thức.
- Cơ chế xác thực chính thức.
- ID mùa vụ thật.
- ID lô thật.
- ID nhân sự thật.
- ID loại công việc thật.

`season_id` hiện có thể dùng mã lô trong chế độ demo khi chưa có bảng ánh xạ. Giá trị này không được mô tả là ID mùa vụ chính thức.

Khi có API và master data NextFarm thật, phải bổ sung mapping:

```text
lot_code → location ID
activity_code → category_task_id
performer_code → assigned_to ID
season_code → season_id
```

---

## 10. Chế độ NextFarm mock và live

Cấu hình trong `.env`:

```env
NEXTFARM_MODE=mock
NEXTFARM_BASE_URL=
NEXTFARM_API_TOKEN=
NEXTFARM_PRODUCTION_DIARY_PATH=/api/diary/production
NEXTFARM_TIMEOUT_SECONDS=10
```

### Mock

```env
NEXTFARM_MODE=mock
```

Chế độ này:

- Không gọi Internet.
- Không cần token.
- Trả kết quả `accepted`.
- Dùng để kiểm thử và demo đồ án.

### Live

```env
NEXTFARM_MODE=live
```

Chế độ này chỉ được dùng khi có:

- URL API thật.
- Token thật.
- Endpoint thật.
- Tài liệu mapping thật.
- Môi trường thử nghiệm được cấp phép.

Không commit token thật vào Git.

---

## 11. Quy trình thay đổi hợp đồng

Khi cần sửa contract:

1. Thành viên đề xuất thay đổi.
2. Nêu rõ lý do.
3. Xác định thành phần bị ảnh hưởng.
4. Cập nhật schema.
5. Cập nhật file ví dụ.
6. Cập nhật model Flutter.
7. Cập nhật Speech/AI output.
8. Cập nhật Pydantic backend.
9. Chạy lại toàn bộ test.
10. Các thành viên xác nhận trước khi merge.

Không tự ý đổi tên trường chỉ trong một service.

Ví dụ thay đổi không tương thích:

```text
lot_code → plot_code
materials → inputs
performed_at → activity_time
```

Các thay đổi này phải tăng `schema_version`.

---

## 12. Kiểm tra trước khi tích hợp

### Speech/AI Service

```text
[ ] Trả đúng snake_case
[ ] Có schema_version
[ ] Có request_id
[ ] Có transcript
[ ] Có missing_fields
[ ] Có warnings
[ ] Không tự quy đổi đơn vị mơ hồ
[ ] Không tự tạo confidence giả
```

### Flutter

```text
[ ] Đọc được AI response
[ ] Hiển thị trường thiếu
[ ] Cho phép sửa dữ liệu
[ ] Tạo client_record_id duy nhất
[ ] Giữ nguyên client_record_id khi retry
[ ] Serialize đúng snake_case
[ ] Gửi confirmed đúng trạng thái
[ ] Lưu SQLite khi offline
[ ] Gửi đúng cấu trúc sync
```

### Integration Service

```text
[ ] Validate đúng schema
[ ] PostgreSQL lưu được dữ liệu
[ ] Không lưu trùng client_record_id
[ ] Sync xử lý riêng từng bản ghi
[ ] Mapper tạo đúng NextFarm payload
[ ] NextFarm mock trả accepted
[ ] Swagger hiển thị đầy đủ endpoint
[ ] Toàn bộ pytest không có FAILED
```

---

## 13. Tiêu chuẩn chốt hợp đồng

Hợp đồng được coi là đã chốt khi:

1. Thắng tạo được JSON đúng AI response schema.
2. Khoa đọc được JSON đó trên Flutter.
3. Khoa chuyển thành cultivation log.
4. Integration Service validate thành công.
5. PostgreSQL lưu thành công.
6. Đồng bộ offline hoạt động.
7. NextFarm mock trả `accepted`.
8. Không thành phần nào phải tự đổi tên trường ngoài contract.
9. Cả ba thành viên xác nhận sử dụng phiên bản `1.0`.

Sau khi chốt phiên bản `1.0`, mọi thay đổi phải được thông báo cho toàn nhóm trước khi merge.