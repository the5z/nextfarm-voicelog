# Dynamic Form Contract V3.1

## 1. Mục đích

Tài liệu này định nghĩa contract/schema dùng chung giữa Frontend, AI Service và Integration Service cho hệ thống NextFarm VoiceLog theo định hướng mới từ phía doanh nghiệp.

Mục tiêu chính:

- Người dùng chọn hoặc nói nghiệp vụ cần thực hiện.
- Frontend hiển thị biểu mẫu tương ứng.
- Người dùng có thể nhập tay hoặc dùng giọng nói.
- AI Service trích xuất dữ liệu đúng theo schema của nghiệp vụ.
- Hệ thống tự điền những gì đã biết từ context.
- AI chỉ hỏi từng field còn thiếu, không hỏi dồn nhiều câu.
- Frontend hiển thị đầy đủ dữ liệu để người dùng kiểm tra.
- Chỉ lưu khi dữ liệu bắt buộc đã đủ và người dùng xác nhận.
- Nếu người dùng bỏ dở, có thể giữ lại phần đã khai để tiếp tục sau.
- AI không tự sinh mã nghiệp vụ; Integration Service chịu trách nhiệm resolve Master Data và validate business rule.

## 2. Phạm vi V3.1

V3.1 thống nhất 7 operation chính:

```text
CREATE_CROP_TYPE
CREATE_SEASON
CREATE_PLOT
CREATE_TASK
CREATE_WORK_LOG
CREATE_ISSUE_REPORT
CREATE_HARVEST
```

| Operation | Nghiệp vụ |
|---|---|
| `CREATE_CROP_TYPE` | Loại cây trồng |
| `CREATE_SEASON` | Mùa vụ |
| `CREATE_PLOT` | Thửa đất |
| `CREATE_TASK` | Công việc |
| `CREATE_WORK_LOG` | Nhật ký làm việc |
| `CREATE_ISSUE_REPORT` | Báo cáo sâu bệnh / bất thường |
| `CREATE_HARVEST` | Khai báo thu hoạch |

## 3. Envelope chung

```json
{
  "contract_version": "3.1",
  "operation": "CREATE_SEASON",
  "template_id": "season",
  "fields": {},
  "missing_fields": [],
  "warnings": [],
  "field_confidence": {},
  "requires_confirmation": false,
  "next_question": null
}
```

## 4. Nguyên tắc kiến trúc

- AI chỉ trả dữ liệu human-readable.
- Integration Service resolve text sang code/ID.
- AI không bịa dữ liệu để làm đầy record.
- Mỗi lần chỉ hỏi một field bắt buộc còn thiếu.
- Tận dụng context: thửa đang mở, mùa vụ đang chạy, cây hiện tại, ngày hiện tại.
- Đọc lại toàn bộ trước khi lưu.
- Nếu người dùng bỏ dở, có thể giữ `current_fields` dưới dạng draft.

## 5. Request từ Frontend sang AI

```json
{
  "operation": "CREATE_SEASON",
  "template_id": "season",
  "transcript": "Tạo vụ dâu mới cho thửa B3",
  "current_fields": {},
  "context": {}
}
```

Voice input dùng multipart/form-data:

```text
audio=<file>
operation=CREATE_SEASON
template_id=season
current_fields=<json>
context=<json>
```

## 6. Context

```json
{
  "current_plot_text": "Thửa B3",
  "current_season_text": "Vụ Dâu 2026",
  "current_crop_text": "Dâu tây",
  "today": "2026-09-09"
}
```

## 7. CREATE_CROP_TYPE

```text
operation: CREATE_CROP_TYPE
template_id: crop_type
```

Required:

```text
crop_name
crop_group_text
crop_code_suggestion
```

Optional:

```text
days_to_harvest
```

Fields:

```json
{
  "crop_name": "Thanh long",
  "crop_group_text": "Cây ăn quả",
  "crop_code_suggestion": "THANH_LONG",
  "days_to_harvest": null
}
```

`crop_code_suggestion` chỉ là gợi ý cho người dùng, không phải business code cuối cùng.

## 8. CREATE_SEASON

```text
operation: CREATE_SEASON
template_id: season
```

Required:

```text
plot_text
crop_text
planting_date_text
season_name
```

Optional:

```text
expected_harvest_date_text
plant_count
expected_yield
expected_yield_unit_text
process_template_text
```

Fields:

```json
{
  "plot_text": "Thửa B3",
  "crop_text": "Dâu tây",
  "planting_date_text": "05/10/2026",
  "season_name": "Vụ Dâu 2026",
  "expected_harvest_date_text": null,
  "plant_count": null,
  "expected_yield": null,
  "expected_yield_unit_text": null,
  "process_template_text": null
}
```

## 9. CREATE_PLOT

```text
operation: CREATE_PLOT
template_id: plot
```

Required:

```text
plot_name_or_code
region_text
boundary_required
```

Optional:

```text
owner_text
current_crop_text
location_hint_text
```

Fields:

```json
{
  "plot_name_or_code": "Thửa B3",
  "region_text": "Khu dưới",
  "boundary_required": true,
  "owner_text": null,
  "current_crop_text": null,
  "location_hint_text": null
}
```

Quy tắc đặc biệt: phần ranh giới phải thực hiện trên bản đồ; AI chỉ hỗ trợ phần text.

## 10. CREATE_TASK

```text
operation: CREATE_TASK
template_id: task
```

Required:

```text
season_text
task_name
task_type_text
due_time_text
```

Optional:

```text
assignee_text
photo_required
note
```

Fields:

```json
{
  "season_text": "Vụ Dâu 2026",
  "task_name": "Phun thuốc khu 2",
  "task_type_text": "Phun",
  "due_time_text": "10/09/2026",
  "assignee_text": null,
  "photo_required": null,
  "note": null
}
```

## 11. CREATE_WORK_LOG

```text
operation: CREATE_WORK_LOG
template_id: work_log
```

Required:

```text
result_status
```

Nếu có nhắc tới vật tư thì bắt buộc đủ:

```text
materials[].material_text
materials[].quantity
materials[].unit_text
```

Optional:

```text
plot_text
activity_text
performed_time_text
photo
material_batch_text
note
```

Fields:

```json
{
  "result_status": "completed",
  "plot_text": "Khu 3",
  "activity_text": "Bón phân",
  "performed_time_text": null,
  "materials": [
    {
      "material_text": "NPK",
      "quantity": 20,
      "unit_text": "kg"
    }
  ],
  "photo_required": false,
  "material_batch_text": null,
  "note": null
}
```

Allowed `result_status`:

```text
completed
partial
failed
```

## 12. CREATE_ISSUE_REPORT

```text
operation: CREATE_ISSUE_REPORT
template_id: issue_report
```

Required:

```text
plot_text
issue_type_text
severity_text
description
```

Optional:

```text
photo
note
```

Issue type:

```text
Sâu
Bệnh
Thời tiết
Tưới tiêu
Khác
```

Severity:

```text
Thấp
Vừa
Cao
Nguy cấp
```

## 13. CREATE_HARVEST

```text
operation: CREATE_HARVEST
template_id: harvest
```

Required:

```text
plot_text
crop_text
quantity
unit_text
harvest_date_text
```

Optional:

```text
photo
note
```

Có thể auto-fill `crop_text` từ mùa vụ đang chạy và `harvest_date_text` mặc định là hôm nay.

## 14. Missing fields

`missing_fields` chỉ chứa field bắt buộc chưa có.

```json
{
  "missing_fields": [
    "crop_text",
    "planting_date_text"
  ]
}
```

Nested field:

```json
{
  "missing_fields": [
    "materials[0].unit_text"
  ]
}
```

## 15. Warnings

Format:

```json
{
  "field": "materials[0].unit_text",
  "code": "AMBIGUOUS_UNIT",
  "message": "Đơn vị 'xị' cần được xác nhận."
}
```

Warning code dự kiến:

```text
AMBIGUOUS_UNIT
LOW_CONFIDENCE
UNKNOWN_MASTER_DATA
CONFLICTING_VALUE
INVALID_FORMAT
BUSINESS_RULE_WARNING
NAME_NOT_MATCHED
```

## 16. Field confidence

```json
{
  "field_confidence": {
    "plot_text": 0.94,
    "crop_text": 0.97,
    "planting_date_text": 0.88
  }
}
```

Ngưỡng UI tham khảo:

```text
>= 0.85      bình thường
0.60 - 0.84  cảnh báo
< 0.60       cần kiểm tra/xác nhận
```

## 17. Next question

AI chỉ hỏi một field bắt buộc tại một thời điểm.

```json
{
  "missing_fields": [
    "crop_text",
    "planting_date_text",
    "season_name"
  ],
  "next_question": "Vụ này trồng cây gì?"
}
```

## 18. Multi-turn / current_fields

Frontend gửi dữ liệu hiện có cùng câu trả lời mới:

```json
{
  "operation": "CREATE_SEASON",
  "template_id": "season",
  "current_fields": {
    "plot_text": "Thửa B3",
    "crop_text": null,
    "planting_date_text": null,
    "season_name": null
  },
  "transcript": "Dâu tây"
}
```

AI giữ dữ liệu cũ và chỉ cập nhật field có căn cứ từ input mới.

## 19. Draft / unfinished flow

Trạng thái dự kiến:

```text
draft
confirmed
saved
cancelled
```

Cách lưu draft cụ thể cần Frontend và Integration Service thống nhất thêm.

## 20. Voice pipeline

```text
Push-to-talk
-> Audio preprocessing
-> Whisper
-> Safe Transcript Correction
-> Name/Domain Dictionary
-> Dynamic Extraction
-> Missing / Warning / Confidence
-> Auto-fill Form
-> User Confirm
```

## 21. Từ điển tên riêng

Dictionary/context theo từng nông trại có thể gồm:

```text
Tên thửa
Tên khu
Tên thiết bị
Tên cây trồng
Tên mùa vụ
Tên vật tư
Tên nhân sự
```

Nếu có nhiều lựa chọn hợp lý thì không tự sửa.

## 22. Giọng vùng miền

Giai đoạn đầu benchmark một số mẫu đại diện:

```text
Bắc
Trung
Nam
```

Đánh giá:

- Speech-to-Text
- Safe Transcript Correction
- Extraction cuối cùng

Không gọi đây là fine-tuning Whisper.

## 23. Số, ngày và đơn vị địa phương

Cần hiểu các cách nói như:

```text
hôm nay
hôm qua
hôm kia
mùng 5
hai khối rưỡi
20 cân
```

Các đơn vị địa phương:

```text
xị
công
sào
```

không tự quy đổi nếu chưa có business rule rõ ràng.

## 24. Confirm-before-save

Chỉ lưu record chính thức khi:

```text
missing_fields = []
confirmed = true
```

Nếu có warning quan trọng thì vẫn phải yêu cầu xác nhận.

## 25. Integration mapping

AI:

```json
{
  "plot_text": "Thửa B3",
  "crop_text": "Dâu tây"
}
```

Integration:

```text
text
-> Master Data Resolve
-> code/ID
-> Business Validation
-> Persist
```

## 26. Trách nhiệm Frontend

- Chọn nghiệp vụ.
- Dynamic Form.
- Auto-fill.
- Highlight missing/warning/confidence.
- Sửa tay.
- Push-to-talk.
- Map cho thửa đất.
- Ảnh cho nghiệp vụ phù hợp.
- Confirm.
- Gửi dữ liệu xác nhận sang Integration.

## 27. Trách nhiệm AI Service

- Speech-to-Text.
- Safe Transcript Correction.
- Dictionary/context tên riêng.
- Dynamic Extraction.
- Merge `current_fields`.
- Missing field.
- Warning.
- Confidence.
- `next_question`.
- Không sinh business code.

## 28. Trách nhiệm Integration Service

- Required/optional business schema.
- Master Data.
- Resolve text -> code/ID.
- Business Validation.
- Context API.
- CRUD.
- Database mapping.
- Confirm-before-save.
- Draft persistence nếu triển khai.

## 29. Quy tắc thay đổi Contract

Mọi thay đổi về operation, template, field, required field hoặc format request/response phải:

```text
1. Cập nhật contract.
2. Cả nhóm thống nhất.
3. Sửa Frontend.
4. Sửa AI Service.
5. Sửa Integration Service.
6. Test end-to-end.
```

## 30. Thứ tự triển khai

Theo tài liệu doanh nghiệp:

```text
1. Nhật ký làm việc
2. Báo cáo sâu bệnh
3. Công việc
4. Thu hoạch
5. Mùa vụ
6. Loại cây trồng
7. Thửa đất
```

Triển khai từ nghiệp vụ ít ràng buộc tới nghiệp vụ phức tạp hơn.

## 31. Trạng thái

```text
Contract version: 3.1
Status: Draft for team implementation
Project: NextFarm VoiceLog
Source direction: NextFarm voice assistant v0.1 - 09/09/2026
```
