# NextFarm VoiceLog AI Service

AI service cho hệ thống NextFarm VoiceLog.

Service chịu trách nhiệm xử lý giọng nói tiếng Việt, chuyển giọng nói thành văn bản bằng Whisper, chuẩn hóa transcript và trích xuất dữ liệu nghiệp vụ bằng Gemini theo Dynamic Form Contract V3.1.

---

## 1. Chức năng chính

AI Service hiện hỗ trợ:

- Upload file âm thanh.
- Tiền xử lý / giảm nhiễu âm thanh.
- Speech-to-Text bằng OpenAI Whisper.
- Sửa một số lỗi transcript phổ biến trong ngữ cảnh nông nghiệp.
- Trích xuất dữ liệu bằng Gemini.
- Hỗ trợ hội thoại nhiều lượt bằng `current_fields`.
- Hỗ trợ context từ frontend/backend.
- Tự động xác định `missing_fields`.
- Sinh `next_question` theo rule deterministic.
- Global exception handlers.
- Request tracking bằng `X-Request-ID`.
- Automated tests bằng pytest.

---

## 2. Các operation hỗ trợ

Dynamic Form V3.1 hiện hỗ trợ 7 operation:

```text
CREATE_CROP_TYPE
CREATE_SEASON
CREATE_PLOT
CREATE_TASK
CREATE_WORK_LOG
CREATE_ISSUE_REPORT
CREATE_HARVEST