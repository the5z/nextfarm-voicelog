# Integration Service

Dịch vụ trung gian nhận nhật ký canh tác đã được người dùng xác nhận,
kiểm tra dữ liệu nghiệp vụ, lưu dữ liệu và mô phỏng đồng bộ với NextFarm.

## Chức năng dự kiến

- Kiểm tra dữ liệu nhật ký.
- Lưu nhật ký canh tác.
- Chống lưu trùng.
- Đồng bộ dữ liệu ngoại tuyến.
- Xuất JSON mô phỏng NextFarm.

## Chạy dự án

```bash
python -m venv .venv
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8002