# Dynamic Form Contract V3

## 1. Mục đích

Tài liệu này định nghĩa contract/schema dùng chung giữa Frontend, AI Service và Integration Service cho hệ thống NextFarm VoiceLog phiên bản nâng cấp theo hướng:

- Người dùng chọn nghiệp vụ.
- Frontend hiển thị biểu mẫu tương ứng.
- Người dùng có thể nhập tay hoặc dùng giọng nói.
- AI Service chỉ trích xuất dữ liệu đúng theo schema của nghiệp vụ đã chọn.
- Frontend tự động điền dữ liệu vào Form.
- Integration Service chịu trách nhiệm resolve Master Data, validate nghiệp vụ và lưu dữ liệu.
- AI không tự sinh mã nghiệp vụ.

Contract này là nguồn tham chiếu chung của cả nhóm. Khi muốn thay đổi tên field, thêm field hoặc đổi cấu trúc request/response, cần cập nhật tài liệu này trước rồi mới sửa code.

---

## 2. Nguyên tắc kiến trúc

### 2.1. AI chỉ trả dữ liệu người đọc được

AI Service trả các giá trị dạng text hoặc primitive để người dùng có thể hiểu và kiểm tra.

Ví dụ đúng:

```json
{
  "activity_text": "Tưới nước",
  "lot_text": "Lô B"
}
```

AI không được tự sinh:

```json
{
  "activity_code": "TUOI_NUOC",
  "lot_code": "LO_B"
}
```

Việc ánh xạ:

```text
"Tưới nước" -> TUOI_NUOC
"Lô B"      -> LO_B
```

là trách nhiệm của Integration Service thông qua Master Data.

### 2.2. Template quyết định schema AI được phép điền

Khi người dùng chọn một nghiệp vụ, Frontend gửi:

```json
{
  "operation": "CREATE_CULTIVATION_LOG",
  "template_id": "cultivation_log"
}
```

AI Service chỉ được trích xuất các field thuộc template đó.

### 2.3. Frontend không tự đổi tên field

Frontend phải dùng đúng field key trong contract.

### 2.4. Integration không tự đổi schema response

Integration Service có thể ánh xạ, validate và lưu dữ liệu nội bộ nhưng không được tự ý thay đổi contract dùng chung giữa các service.

---

## 3. Envelope chung

Mọi response từ AI Service theo Contract V3 có cấu trúc:

```json
{
  "contract_version": "3.0",
  "operation": "CREATE_CULTIVATION_LOG",
  "template_id": "cultivation_log",
  "fields": {},
  "missing_fields": [],
  "warnings": [],
  "field_confidence": {},
  "requires_confirmation": false
}
```

### Ý nghĩa

| Field | Ý nghĩa |
|---|---|
| `contract_version` | Phiên bản contract |
| `operation` | Nghiệp vụ đang thực hiện |
| `template_id` | Mẫu Form tương ứng |
| `fields` | Dữ liệu nghiệp vụ đã trích xuất |
| `missing_fields` | Các field bắt buộc còn thiếu |
| `warnings` | Cảnh báo nghiệp vụ hoặc dữ liệu mơ hồ |
| `field_confidence` | Độ tin cậy theo từng field |
| `requires_confirmation` | Có cần người dùng xác nhận hay không |

---

## 4. Các operation giai đoạn đầu

Giai đoạn đầu thống nhất 4 operation:

```text
CREATE_CULTIVATION_LOG
CREATE_SEASON
CREATE_PLOT
CREATE_MATERIAL_RECEIPT
```

---

## 5. Template: Ghi nhật ký canh tác

### 5.1. Thông tin template

```text
operation:   CREATE_CULTIVATION_LOG
template_id: cultivation_log
```

### 5.2. Fields

```json
{
  "activity_text": "Bón phân",
  "lot_text": "Lô A",
  "materials": [
    {
      "material_text": "NPK",
      "quantity": 20,
      "unit_text": "kg"
    }
  ],
  "performed_time_text": "08:00",
  "note": null
}
```

### 5.3. Response mẫu

```json
{
  "contract_version": "3.0",
  "operation": "CREATE_CULTIVATION_LOG",
  "template_id": "cultivation_log",
  "fields": {
    "activity_text": "Bón phân",
    "lot_text": "Lô A",
    "materials": [
      {
        "material_text": "NPK",
        "quantity": 20,
        "unit_text": "kg"
      }
    ],
    "performed_time_text": "08:00",
    "note": null
  },
  "missing_fields": [],
  "warnings": [],
  "field_confidence": {
    "activity_text": 0.98,
    "lot_text": 0.95,
    "materials[0].material_text": 0.96,
    "materials[0].quantity": 0.99,
    "materials[0].unit_text": 0.94,
    "performed_time_text": 0.91
  },
  "requires_confirmation": false
}
```

---

## 6. Template: Tạo vụ mùa

### 6.1. Thông tin template

```text
operation:   CREATE_SEASON
template_id: season
```

### 6.2. Fields

```json
{
  "season_name": "Vụ Đông Xuân 2026",
  "crop_text": "Lúa",
  "start_date_text": "15/09/2026",
  "expected_end_date_text": null,
  "note": null
}
```

### 6.3. Response mẫu

```json
{
  "contract_version": "3.0",
  "operation": "CREATE_SEASON",
  "template_id": "season",
  "fields": {
    "season_name": "Vụ Đông Xuân 2026",
    "crop_text": "Lúa",
    "start_date_text": "15/09/2026",
    "expected_end_date_text": null,
    "note": null
  },
  "missing_fields": [
    "expected_end_date_text"
  ],
  "warnings": [],
  "field_confidence": {
    "season_name": 0.96,
    "crop_text": 0.94,
    "start_date_text": 0.92,
    "expected_end_date_text": null
  },
  "requires_confirmation": true
}
```

---

## 7. Template: Tạo thửa/lô đất

### 7.1. Thông tin template

```text
operation:   CREATE_PLOT
template_id: plot
```

### 7.2. Fields

```json
{
  "plot_name": "Lô C",
  "area": 2500,
  "area_unit_text": "m2",
  "location_text": "Khu phía Đông",
  "note": null
}
```

### 7.3. Response mẫu

```json
{
  "contract_version": "3.0",
  "operation": "CREATE_PLOT",
  "template_id": "plot",
  "fields": {
    "plot_name": "Lô C",
    "area": 2500,
    "area_unit_text": "m2",
    "location_text": "Khu phía Đông",
    "note": null
  },
  "missing_fields": [],
  "warnings": [],
  "field_confidence": {
    "plot_name": 0.98,
    "area": 0.93,
    "area_unit_text": 0.96,
    "location_text": 0.84
  },
  "requires_confirmation": true
}
```

---

## 8. Template: Nhập vật tư

### 8.1. Thông tin template

```text
operation:   CREATE_MATERIAL_RECEIPT
template_id: material_receipt
```

### 8.2. Fields

```json
{
  "material_text": "NPK",
  "quantity": 50,
  "unit_text": "kg",
  "received_date_text": "09/09/2026",
  "supplier_text": null,
  "note": null
}
```

### 8.3. Response mẫu

```json
{
  "contract_version": "3.0",
  "operation": "CREATE_MATERIAL_RECEIPT",
  "template_id": "material_receipt",
  "fields": {
    "material_text": "NPK",
    "quantity": 50,
    "unit_text": "kg",
    "received_date_text": "09/09/2026",
    "supplier_text": null,
    "note": null
  },
  "missing_fields": [],
  "warnings": [],
  "field_confidence": {
    "material_text": 0.97,
    "quantity": 0.99,
    "unit_text": 0.98,
    "received_date_text": 0.92,
    "supplier_text": null
  },
  "requires_confirmation": false
}
```

---

## 9. Template definition cho Frontend

Frontend có thể dùng cấu hình template để dựng Dynamic Form.

Ví dụ:

```json
{
  "template_id": "cultivation_log",
  "title": "Ghi nhật ký canh tác",
  "fields": [
    {
      "key": "activity_text",
      "label": "Hoạt động",
      "type": "select",
      "required": true
    },
    {
      "key": "lot_text",
      "label": "Lô sản xuất",
      "type": "select",
      "required": true
    },
    {
      "key": "materials",
      "label": "Vật tư",
      "type": "material_list",
      "required": false
    },
    {
      "key": "performed_time_text",
      "label": "Thời gian",
      "type": "datetime",
      "required": true
    },
    {
      "key": "note",
      "label": "Ghi chú",
      "type": "textarea",
      "required": false
    }
  ]
}
```

Frontend cần tối thiểu:

```text
key
label
type
required
```

để dựng Form.

---

## 10. Request từ Frontend sang AI Service

### 10.1. Text input

```json
{
  "operation": "CREATE_CULTIVATION_LOG",
  "template_id": "cultivation_log",
  "transcript": "Bón 20kg NPK ở lô A lúc 8 giờ"
}
```

### 10.2. Voice input

Frontend gửi audio kèm metadata:

```text
audio=<file>
operation=CREATE_CULTIVATION_LOG
template_id=cultivation_log
```

Pipeline AI:

```text
Audio
-> FFmpeg preprocessing
-> Whisper
-> Safe Transcript Correction
-> Schema-aware Extraction
-> Confidence / Uncertainty
-> Contract V3
```

---

## 11. Bổ sung dữ liệu nhiều lượt

Khi người dùng đã có một phần dữ liệu trong Form và nói bổ sung, Frontend gửi thêm `current_fields`.

Ví dụ:

```json
{
  "operation": "CREATE_CULTIVATION_LOG",
  "template_id": "cultivation_log",
  "current_fields": {
    "activity_text": "Bón phân",
    "lot_text": "Lô A",
    "materials": [
      {
        "material_text": "NPK",
        "quantity": null,
        "unit_text": null
      }
    ],
    "performed_time_text": null
  },
  "transcript": "20 ký lúc 8 giờ"
}
```

AI chỉ cập nhật các field có thể xác định từ input mới, không được tự xóa giá trị cũ nếu không có căn cứ rõ ràng.

---

## 12. Missing fields

`missing_fields` dùng cho field bắt buộc nhưng chưa có giá trị.

Ví dụ:

```json
{
  "missing_fields": [
    "lot_text",
    "performed_time_text"
  ]
}
```

Với danh sách lồng nhau:

```json
{
  "missing_fields": [
    "materials[0].quantity",
    "materials[0].unit_text"
  ]
}
```

Frontend dùng danh sách này để highlight các ô cần bổ sung.

---

## 13. Warnings

`warnings` dùng khi đã có dữ liệu nhưng dữ liệu có vấn đề hoặc chưa đủ chắc chắn.

Format:

```json
{
  "warnings": [
    {
      "field": "unit_text",
      "code": "AMBIGUOUS_UNIT",
      "message": "Đơn vị 'xị' chưa thể quy đổi tự động."
    }
  ]
}
```

Một số warning code dự kiến:

```text
AMBIGUOUS_UNIT
LOW_CONFIDENCE
UNKNOWN_MASTER_DATA
CONFLICTING_VALUE
INVALID_FORMAT
BUSINESS_RULE_WARNING
```

Các đơn vị hoặc khái niệm mơ hồ như `xị`, `công`, `sào` không được tự động quy đổi nếu không có rule nghiệp vụ rõ ràng.

---

## 14. Field confidence

Confidence được trả theo từng field.

Ví dụ:

```json
{
  "field_confidence": {
    "activity_text": 0.97,
    "lot_text": 0.92,
    "materials[0].material_text": 0.96,
    "materials[0].quantity": 0.99,
    "materials[0].unit_text": 0.88
  }
}
```

Ngưỡng tham khảo cho UI:

```text
>= 0.85      bình thường
0.60 - 0.84  cảnh báo
< 0.60       yêu cầu kiểm tra/xác nhận
```

Các ngưỡng này chỉ là baseline ban đầu và có thể điều chỉnh sau benchmark.

---

## 15. Requires confirmation

`requires_confirmation = true` khi có ít nhất một trong các điều kiện:

- Có `missing_fields`.
- Có warning nghiêm trọng.
- Có field confidence thấp.
- Có dữ liệu được AI suy ra nhưng cần người dùng kiểm tra.
- Có thay đổi dữ liệu hiện có trong Form.

Ví dụ:

```json
{
  "requires_confirmation": true
}
```

---

## 16. Luồng xác nhận và lưu dữ liệu

```text
User chọn nghiệp vụ
        |
        v
Frontend load template
        |
        v
User nhập tay / nói
        |
        v
AI Service
        |
        v
Contract V3
        |
        v
Frontend auto-fill
        |
        v
User review / chỉnh sửa
        |
        v
Confirm
        |
        v
Integration Service
        |
        +-> Master Data Resolve
        +-> Business Validation
        +-> Canonical Mapping
        |
        v
PostgreSQL / NextFarm
```

---

## 17. Trách nhiệm từng thành phần

### Frontend

- Hiển thị danh sách nghiệp vụ.
- Load template.
- Render Dynamic Form.
- Gửi `operation` và `template_id` cho AI.
- Auto-fill dữ liệu AI trả về.
- Hiển thị missing field.
- Hiển thị warning.
- Cho phép người dùng chỉnh tay.
- Chỉ gửi dữ liệu sang Integration sau khi người dùng xác nhận.

### AI Service

- Nhận `operation` và `template_id`.
- Xử lý audio.
- Speech-to-Text.
- Safe Transcript Correction.
- Chỉ extract field thuộc schema đang chọn.
- Không sinh business code.
- Trả missing field.
- Trả warning.
- Trả field confidence.
- Hỗ trợ merge dữ liệu nhiều lượt thông qua `current_fields`.

### Integration Service

- Nhận dữ liệu đã được người dùng xác nhận.
- Resolve Master Data.
- Ánh xạ text sang code nội bộ.
- Validate business rule.
- Chuẩn hóa dữ liệu canonical.
- Tạo/sửa dữ liệu trong PostgreSQL.
- Chuẩn bị tích hợp với NextFarm thật.

---

## 18. Quy tắc thay đổi Contract

Mọi thay đổi liên quan đến:

- tên field,
- field bắt buộc,
- template mới,
- operation mới,
- format warning,
- format confidence,
- request/response schema

đều phải:

```text
1. Cập nhật file contract.
2. Cả nhóm thống nhất.
3. Sửa Frontend.
4. Sửa AI Service.
5. Sửa Integration Service.
6. Chạy test end-to-end.
```

Không tự ý sửa riêng ở một service.

---

## 19. Phân công hiện tại

| Thành viên | Phần phụ trách |
|---|---|
| Thắng | AI Service, schema-aware extraction, confidence, missing, warnings, voice pipeline |
| Khoa | Dynamic Form, chọn nghiệp vụ, auto-fill, mobile UI, hiển thị trạng thái |
| Hiệp | Business schema, Master Data, validation, CRUD, database, integration |
| Cả nhóm | Contract V3, field naming, API contract, end-to-end testing |

---

## 20. Phạm vi V3 giai đoạn 1

Giai đoạn đầu chỉ triển khai và test:

```text
CREATE_CULTIVATION_LOG
CREATE_SEASON
CREATE_PLOT
CREATE_MATERIAL_RECEIPT
```

Sau khi 4 nghiệp vụ trên ổn định mới mở rộng thêm nghiệp vụ khác.

---

## 21. Trạng thái

```text
Contract version: 3.0
Status: Draft for team implementation
Project: NextFarm VoiceLog
```
