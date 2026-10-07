"""
Pytest fixtures shared across all test modules.

Key decisions:
- A fresh in-memory SQLite database is created per test session so tests are
  isolated from the production database.
- The Celery task (process_certificate_job) is called synchronously via
  CELERY_TASK_ALWAYS_EAGER so tests don't need a running Redis/worker.
- Environment variables that point to the test DB are patched before the app
  is imported so the same settings object is used throughout.
"""

import os
import tempfile
import shutil
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---- Patch settings BEFORE importing anything from app ----
TEST_DB_FILE = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["CELERY_TASK_EAGER_PROPAGATES"] = "true"

from app.main import app
from app.database import get_db
from app.models import Base
from app.celery_app import celery_app as _celery_app

# Configure Celery to run tasks synchronously (no broker needed)
_celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(
        f"sqlite:///{TEST_DB_FILE}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    # On Windows the SQLite file may still be held by the process; ignore the error.
    try:
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)
    except PermissionError:
        pass


@pytest.fixture()
def db_session(test_db_engine):
    """Yield a database session that is rolled back after each test."""
    TestingSession = sessionmaker(bind=test_db_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(test_db_engine, tmp_path, monkeypatch):
    """
    FastAPI TestClient with:
    - DB overridden to the test SQLite engine
    - CERTIFICATES_DIR redirected to a temp directory
    """
    TestingSession = sessionmaker(bind=test_db_engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Redirect generated PDFs to a temp dir so they're cleaned up automatically
    monkeypatch.setenv("CERTIFICATES_DIR", str(tmp_path))
    from app import config as cfg_module
    from app import certificate_generator as gen_module
    monkeypatch.setattr(cfg_module.settings, "CERTIFICATES_DIR", str(tmp_path))
    monkeypatch.setattr(gen_module.settings, "CERTIFICATES_DIR", str(tmp_path))

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
