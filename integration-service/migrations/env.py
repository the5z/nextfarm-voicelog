from __future__ import annotations

from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

# Import toàn bộ model trước khi lấy Base.metadata.
# Nếu không import model, metadata có thể không chứa bảng nào.
import app.models  # noqa: F401

from app.database import DATABASE_URL
from app.models.base import Base


# Đối tượng cấu hình Alembic, đọc từ alembic.ini.
config = context.config


# Cấu hình logging theo nội dung trong alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Không lưu mật khẩu PostgreSQL trong alembic.ini.
# Alembic sẽ sử dụng DATABASE_URL đã được app.database đọc từ .env.
#
# Dấu % phải được escape thành %% vì ConfigParser dùng %
# cho cơ chế nội suy giá trị.
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.replace("%", "%%"),
)


# Metadata của toàn bộ SQLAlchemy model thuộc Integration Service.
target_metadata = Base.metadata


def include_object(
    object_: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """
    Quy định đối tượng database nào được Alembic quản lý.

    Bỏ qua các bảng chỉ tồn tại trong PostgreSQL nhưng không tồn tại
    trong SQLAlchemy metadata, chẳng hạn:

    - cultivation_logs_legacy
    - cultivation_log_materials_legacy
    - bảng của hệ thống khác nằm chung database

    Các bảng được định nghĩa trong app.models vẫn được quản lý
    và có thể tạo migration bình thường.
    """

    if (
        type_ == "table"
        and reflected
        and compare_to is None
    ):
        return False

    return True


def configure_context(
    *,
    connection: Connection | None = None,
    url: str | None = None,
    literal_binds: bool = False,
) -> None:
    """
    Cấu hình Alembic dùng chung cho chế độ online và offline.
    """

    options: dict[str, Any] = {
        "target_metadata": target_metadata,
        "include_object": include_object,
        "compare_type": True,
        "compare_server_default": True,
        "include_schemas": False,
    }

    if connection is not None:
        options["connection"] = connection

    if url is not None:
        options["url"] = url
        options["literal_binds"] = literal_binds
        options["dialect_opts"] = {
            "paramstyle": "named",
        }

    context.configure(**options)


def run_migrations_offline() -> None:
    """
    Chạy migration ở chế độ offline.

    Chế độ này tạo câu lệnh SQL mà không cần mở kết nối trực tiếp
    tới PostgreSQL.
    """

    database_url = config.get_main_option(
        "sqlalchemy.url"
    )

    configure_context(
        url=database_url,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Chạy migration trực tiếp trên PostgreSQL.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        configure_context(
            connection=connection,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()