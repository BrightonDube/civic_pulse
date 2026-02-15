"""Shared test fixtures for backend tests."""
import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models import User, Report, Upvote  # noqa: F401 - ensure all models are registered

# Single shared engine for all tests - ensures TestClient and tests see same data
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def _setup_tables():
    """Create and drop tables for each test."""
    Base.metadata.create_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)


@pytest.fixture
def db_engine():
    """Return the shared test engine."""
    return _test_engine


@pytest.fixture
def db_session():
    """Create a test database session."""
    Session = sessionmaker(bind=_test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client():
    """Create a FastAPI test client with overridden db dependency."""
    Session = sessionmaker(bind=_test_engine)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
