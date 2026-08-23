# NextFarm VoiceLog

Hệ thống ghi nhật ký sản xuất nông nghiệp bằng giọng nói tiếng Việt cho NextFarm.

## Tổng quan

NextFarm VoiceLog hỗ trợ người dùng ghi nhật ký canh tác bằng giọng nói. Hệ thống xử lý audio, chuyển giọng nói thành văn bản, chuẩn hóa transcript, trích xuất dữ liệu bằng AI, kiểm tra thông tin còn thiếu, hỏi bổ sung qua VoiceLog Bot, resolve Master Data và lưu nhật ký thông qua Integration Service.

Hệ thống cũng có Query Assistant để tra cứu nhật ký bằng ngôn ngữ tự nhiên.

## Kiến trúc

```text
Frontend - React + Vite
        |
        | audio / message
        v
AI Service - FastAPI
        |
        |-- FFmpeg preprocessing
        |-- Whisper Speech-to-Text
        |-- Safe Transcript Correction
        |-- Gemini Extraction
        |-- Confidence / Uncertainty
        |-- Missing Fields Detection
        |-- VoiceLog Bot
        |-- Query Assistant
        |
        | Text Contract V2
        v
Integration Service - FastAPI
        |
        |-- Master Data Resolve
        |-- Business Validation
        |-- Cultivation Logs
        |-- Sync / NextFarm Adapter
        v
PostgreSQL 16
        |
        v
NextFarm Backend / Mock
```

LLM không được phép tự tạo mã nghiệp vụ. AI Service truyền dữ liệu dạng human-readable; Integration Service chịu trách nhiệm resolve sang Master Data code.

## Text Contract V2

```json
{
  "activity_text": "Tưới nước",
  "lot_text": "Lô B",
  "materials": [
    {
      "material_text": "Nước",
      "quantity": 100,
      "unit_text": "lít"
    }
  ],
  "time_text": "06:00",
  "missing_fields": [],
  "warnings": [],
  "requires_confirmation": false
}
```

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Frontend | React 19, Vite 8 |
| AI Service | FastAPI, Uvicorn, Pydantic |
| Speech-to-Text | OpenAI Whisper |
| LLM | Google Gemini (`google-genai`) |
| Integration Service | FastAPI, SQLAlchemy 2 |
| Database | PostgreSQL 16 |
| PostgreSQL Driver | Psycopg 3 |
| Migration | Alembic |
| Testing | pytest, frontend Node tests |
| Container | Docker Compose |
| API Testing | Postman |

## Cấu trúc repository

```text
nextfarm-voicelog/
|-- frontend/
|   |-- public/
|   |-- src/
|   |-- package.json
|   `-- vite.config.js
|-- ai-service/
|   |-- app/
|   |-- benchmark/
|   |-- tests/
|   |-- uploads/
|   |-- Dockerfile
|   `-- requirements.txt
|-- integration-service/
|   |-- app/
|   |-- migrations/
|   |-- tests/
|   |-- alembic.ini
|   `-- requirements.txt
|-- contracts/
|-- docs/
|-- postman/
|-- scripts/
|-- uploads/
|-- docker-compose.yml
|-- CONTRIBUTING.md
|-- README.md
`-- .gitignore
```

## Thành viên

| Thành viên | Phụ trách |
|---|---|
| Hiệp | Integration Service, NextFarm API, Master Data, lưu và đồng bộ dữ liệu |
| Thắng | Backend AI / AI Service: FastAPI, Whisper, Gemini, Validation, VoiceLog Bot |
| Khoa | Frontend React/Vite, giao diện VoiceLog và AI Assistant |

## Port

| Service | Địa chỉ |
|---|---|
| Frontend | `http://localhost:5173` |
| AI Service | `http://127.0.0.1:8000` |
| AI Swagger | `http://127.0.0.1:8000/docs` |
| Integration Service | `http://127.0.0.1:8002` |
| Integration Swagger | `http://127.0.0.1:8002/docs` |
| PostgreSQL host port | `1275` |

## Chạy hệ thống

### 1. PostgreSQL

Từ thư mục root:

```powershell
docker compose up -d postgres
docker ps
```

PostgreSQL container hiện dùng tên `nextfarm-postgres`.

### 2. AI Service

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --port 8000
```

Không dùng `--reload` trên máy RAM hạn chế vì Whisper có thể bị load nhiều lần.

### 3. Integration Service

Mở terminal mới:

```powershell
cd integration-service
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --port 8002
```

### 4. Frontend

Mở terminal mới:

```powershell
cd frontend
npm install
npm run dev
```

Nếu dependency đã được cài trước đó:

```powershell
npm run dev
```

## AI Service API

Các endpoint hiện có:

```text
POST /api/v1/audio/upload
POST /api/v1/bot/sessions
GET  /api/v1/bot/sessions/{session_id}
POST /api/v1/bot/sessions/{session_id}/messages
GET  /api/v1/health
GET  /api/v1/ready
```

## Integration Service API

Các endpoint chính:

```text
/api/cultivation-logs
/api/cultivation-logs/test
/api/cultivation-logs/validate
/api/cultivation-logs/{client_record_id}
/api/history
/api/master-data/activities
/api/master-data/lots
/api/master-data/materials
/api/master-data/resolve
/api/master-data/resolve-cultivation
/api/master-data/units
/api/nextfarm/cultivation-logs/{client_record_id}/submit
/api/nextfarm/test
/api/sync/logs
/api/sync/test
/health
```

## Master Data

### Activities

```text
BON_PHAN
PHUN_THUOC
TUOI_NUOC
LAM_CO
THU_HOACH
CHO_BO_AN
```

### Lots

```text
Lô A -> LO_A
Lô B -> LO_B
```

### Materials

```text
Cám -> CAM
NPK -> NPK
Urê -> URE
```

### Units

```text
KG
G
L
ML
BAG
BOTTLE
```

Các đơn vị mơ hồ như `xị`, `công`, `sào` không được tự động quy đổi nếu chưa có quy tắc nghiệp vụ rõ ràng.

`materials` có thể là mảng rỗng đối với hoạt động không sử dụng vật tư.

## Query Assistant

Ví dụ câu hỏi hỗ trợ:

```text
Cho tôi xem nhật ký gần nhất
Hôm nay có những hoạt động gì?
Cho tôi xem nhật ký hôm qua
7 ngày gần đây có những hoạt động gì?
Có bao nhiêu lần bón phân?
Lô A đã bón phân bao nhiêu lần?
7 ngày gần đây Lô A có những hoạt động gì?
7 ngày gần đây Lô A có bao nhiêu lần bón phân?
NPK đã được dùng ở lô nào?
7 ngày gần đây NPK đã được dùng ở lô nào?
```

Các truy vấn ngày hiện được xử lý theo thời gian Việt Nam UTC+7.

Intent Router ưu tiên nhận diện Query để câu hỏi tra cứu không bị VoiceLog Bot hiểu nhầm thành giá trị của field đang thiếu.

## Testing

### Frontend

```powershell
cd frontend
node src/services/intentRouter.test.js
node src/services/queryService.test.js
node src/services/queryAssistantService.test.js
npm run build
```

### AI Service

```powershell
cd ai-service
.\.venv\Scripts\Activate.ps1
pytest
```

### Integration Service

```powershell
cd integration-service
.\.venv\Scripts\Activate.ps1
pytest
```

## Demo checklist

```text
[ ] PostgreSQL đang chạy
[ ] AI Service đang chạy ở port 8000
[ ] Integration Service đang chạy ở port 8002
[ ] Frontend đang chạy ở port 5173
[ ] AI Swagger truy cập được
[ ] Integration Swagger truy cập được
[ ] VoiceLog flow hoạt động
[ ] Query Assistant hoạt động
```

Luồng demo VoiceLog:

```text
Audio
 -> FFmpeg
 -> Whisper
 -> Transcript Correction
 -> Gemini Extraction
 -> Confidence / Missing Fields
 -> VoiceLog Bot hỏi bổ sung nếu cần
 -> User Confirmation
 -> Text Contract V2
 -> Integration Service
 -> Master Data Resolve
 -> Business Validation
 -> PostgreSQL
```

Regression quan trọng: trong lúc VoiceLog Bot đang hỏi một field còn thiếu, một câu query như `Cho tôi xem nhật ký hôm nay` phải đi vào Query Assistant và không được điền nhầm vào VoiceLog context.

## Git workflow

```text
feature/*
   |
   v
Pull Request
   |
   v
develop
   |
   v
Regression Test
   |
   v
main
```

- `main`: phiên bản ổn định.
- `develop`: branch tích hợp và kiểm thử.
- `feature/*`: branch phát triển tính năng.
- Không commit trực tiếp vào `main`.

## Bảo mật

Không commit các secret như:

```text
.env
API keys
Gemini API key
Database credentials
Private tokens
```

Các secret nên được lấy từ biến môi trường / `.env`; chỉ commit file `.env.example` không chứa giá trị thật.

## Trạng thái chức năng

Hệ thống hiện đã có:

```text
Audio Processing
Whisper Speech-to-Text
Safe Transcript Correction
Gemini Extraction
Confidence / Uncertainty
Missing Fields Detection
VoiceLog Bot
Intent Router
Query Assistant
Today Query
Yesterday Query
Recent 7-Day Query
Combined Time + Business Filters
Master Data Friendly Names
Integration Service
PostgreSQL Persistence
Regression Tests
```

## License

Private project for NextFarm Internship.
