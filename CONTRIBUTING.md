# Contributing Guide

## Quy trình làm việc

### 1. Cập nhật branch develop

```bash
git checkout develop
git pull origin develop
```

### 2. Tạo branch mới

```bash
git checkout -b feature/<ten-tinh-nang>
```

Ví dụ:

```bash
git checkout -b feature/audio-upload
```

### 3. Kiểm tra và commit

```bash
git status
git add .
git commit -m "feat: add audio upload"
```

### 4. Push branch lên GitHub

```bash
git push -u origin feature/audio-upload
```

### 5. Tạo Pull Request

Tạo Pull Request từ branch `feature/*` vào branch `develop`.

Một thành viên khác nên kiểm tra mã nguồn trước khi merge.

## Quy tắc

- Không commit trực tiếp vào `main`.
- Không commit trực tiếp vào `develop` khi đang phát triển tính năng.
- Mỗi tính năng hoặc lỗi nên có một branch riêng.
- Commit theo từng thay đổi nhỏ và rõ ràng.
- Pull branch `develop` mới nhất trước khi bắt đầu công việc.

## Không được commit

- File `.env`
- API key
- Mật khẩu
- Access token
- File model AI dung lượng lớn
- File build
- Thư mục môi trường ảo