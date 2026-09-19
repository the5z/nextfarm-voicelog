from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.database import get_db
from app.main import app
from app.models.base import Base
from app.services.log_service import clear_logs
from app.services.issue_report_service import (
    clear_issue_reports,
)
from app.services.task_service import (
    clear_tasks,
)
from app.services.harvest_service import (
    clear_harvests,
)
from app.services.season_service import (
    clear_seasons,
)
from app.services.crop_type_service import (
    clear_crop_types,
)
from app.services.plot_service import (
    clear_plots,
)
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# Tạo các bảng SQLAlchemy trong database SQLite dùng cho test.
Base.metadata.create_all(bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    """
    Thay kết nối PostgreSQL bằng SQLite trong lúc chạy test.
    """

    database_session = TestingSessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


# Mọi endpoint dùng Depends(get_db) sẽ nhận SQLite test database.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_test_database() -> Generator[None, None, None]:
    """
    Tự động xóa dữ liệu trước và sau mỗi bài test.
    """

    with TestingSessionLocal() as database_session:
        clear_tasks(
            database_session
        )
        clear_issue_reports(
            database_session
        )
        clear_logs(
            database_session
        )
        clear_harvests(
            database_session
        )
        clear_seasons(
            database_session
        )
        clear_crop_types(
            database_session
        )
        clear_plots(
            database_session
        )

    yield

    with TestingSessionLocal() as database_session:
        clear_tasks(
            database_session
        )
        clear_issue_reports(
            database_session
        )
        clear_logs(
            database_session
        )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Cung cấp FastAPI TestClient cho các bài test.
    """

    with TestClient(app) as test_client:
        yield test_client