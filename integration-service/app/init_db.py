import app.models  # noqa: F401

from app.database import engine
from app.models.base import Base


def create_database_tables() -> None:
    """Tạo các bảng chưa tồn tại trong PostgreSQL."""

    print("Đang kết nối PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Đã khởi tạo bảng PostgreSQL thành công.")


if __name__ == "__main__":
    create_database_tables()