# nextfarm-voicelog
Vietnamese voice-based farming log system for NextFarm
# NextFarm VoiceLog

Ứng dụng ghi nhật ký sản xuất nông nghiệp bằng giọng nói tiếng Việt.

Người dùng ghi âm nội dung công việc, hệ thống chuyển giọng nói thành văn bản, trích xuất dữ liệu có cấu trúc bằng AI, yêu cầu người dùng xác nhận và lưu vào hệ thống NextFarm.

---

# Mục tiêu

- Ghi nhật ký bằng giọng nói thay cho nhập liệu thủ công.
- Chuyển giọng nói thành văn bản (Speech-to-Text).
- Trích xuất thông tin bằng LLM.
- Kiểm tra dữ liệu trước khi lưu.
- Đồng bộ với hệ thống NextFarm.

---

# Kiến trúc hệ thống

```text
Audio
  ↓
Flutter Frontend
  ↓
AI Service
  ├── Speech-to-Text
  ├── LLM Extraction
  └── Validation
  ↓
User Confirmation
  ↓
Integration Service
  ↓
NextFarm Backend
```

---

# Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Frontend | Flutter |
| Backend AI | FastAPI |
| Speech-to-Text | Whisper / PhoWhisper |
| LLM | Qwen hoặc GPT |
| Database | NextFarm Database |
| Local Storage | SQLite |
| API Testing | Postman |
| Container | Docker |

---

# Cấu trúc Repository

```text
nextfarm-voicelog/
│
├── frontend/               # Flutter App
├── ai-service/             # FastAPI + AI
├── integration-service/    # NextFarm Integration
├── docs/                   # Documentation
├── postman/                # API Collection
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# Thành viên

| Thành viên | Phụ trách |
|------------|------------|
| Hiệp | Flutter Frontend, ghi âm, giao diện xác nhận, SQLite |
| Thắng | AI Service, FastAPI, Whisper, LLM, Validation |
| Khoa | Integration Service, NextFarm API, đồng bộ dữ liệu |

---

# Luồng xử lý

```text
Audio
    ↓
Speech-to-Text
    ↓
Transcript
    ↓
LLM
    ↓
Structured JSON
    ↓
Validation
    ↓
User Confirmation
    ↓
Save to NextFarm
```

**Lưu ý**

LLM **không được phép lưu dữ liệu trực tiếp**.

Mọi dữ liệu đều phải:

1. Validation
2. Người dùng xác nhận
3. Sau đó mới lưu.

---

# Git Workflow

## Main Branch

```
main
```

Chứa phiên bản ổn định.

---

## Develop Branch

```
develop
```

Dùng để tích hợp các tính năng.

---

## Feature Branch

```
feature/frontend

feature/backend-ai

feature/integration
```

Mỗi thành viên làm việc trên branch riêng.

---

# Quy trình làm việc

```text
feature/*
      │
      ▼
Pull Request
      │
      ▼
develop
      │
      ▼
Testing
      │
      ▼
main
```

Không commit trực tiếp vào `main`.

---

# Quy ước Commit

Ví dụ:

```
feat: add speech-to-text endpoint

feat: implement whisper service

fix: handle invalid audio

docs: update api contract

refactor: optimize validation

test: add ai unit tests

chore: initialize project structure
```

---

# Quy tắc làm việc

1. Luôn pull `develop` trước khi làm việc.
2. Mỗi tính năng tạo một branch riêng.
3. Không push trực tiếp vào `main`.
4. Merge thông qua Pull Request.
5. Review code trước khi merge.
6. Không commit API Key hoặc file `.env`.

---

# Roadmap

## Phase 1

- Repository Setup
- Git Workflow
- API Design

## Phase 2

- Flutter UI
- AI Backend
- Integration Service

## Phase 3

- Whisper
- LLM Extraction
- Validation

## Phase 4

- End-to-End Testing
- Docker
- Deployment

---

# License

Private project for NextFarm Internship.