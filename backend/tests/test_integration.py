"""
Integration and security tests.

Task 19: Final integration testing
- 19.5: Security testing - auth on protected endpoints, RBAC, rate limiting
"""
import pytest
from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import User, Report, Upvote, StatusHistory, AdminNote, AuditLog  # noqa: F401
from app.services.auth_service import AuthService


# In-memory SQLite for integration tests
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_token():
    """Create a user and return auth token."""
    db = TestSession()
    svc = AuthService(db)
    svc.register_user("user@test.com", "Password123!", "+1234567890")
    token = svc.login("user@test.com", "Password123!")
    db.close()
    return token


@pytest.fixture
def admin_token():
    """Create an admin user and return auth token."""
    db = TestSession()
    svc = AuthService(db)
    user = svc.register_user("admin@test.com", "AdminPass123!", "+1234567890")
    user.role = "admin"
    db.commit()
    token = svc.login("admin@test.com", "AdminPass123!")
    db.close()
    return token


# Task 19.5: Security Testing

class TestAuthProtection:
    """Verify authentication on all protected endpoints."""

    def test_reports_require_auth(self, client):
        """GET /api/reports/ should require authentication."""
        resp = client.get("/api/reports/")
        assert resp.status_code in (401, 403)

    def test_my_reports_require_auth(self, client):
        """GET /api/reports/my should require authentication."""
        resp = client.get("/api/reports/my")
        assert resp.status_code in (401, 403)

    def test_report_creation_requires_auth(self, client):
        """POST /api/reports/ should require authentication."""
        resp = client.post("/api/reports/")
        assert resp.status_code in (401, 403, 422)

    def test_admin_endpoints_require_admin(self, client, user_token):
        """Admin endpoints should reject regular users."""
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.post(
            "/api/admin/reports/some-id/status",
            json={"status": "Fixed"},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_admin_endpoints_accept_admin(self, client, admin_token):
        """Admin endpoints should accept admin users."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.post(
            "/api/admin/reports/some-id/status",
            json={"status": "Fixed"},
            headers=headers,
        )
        # Should fail with 400 (invalid UUID), not 403
        assert resp.status_code == 400


class TestRBACIntegration:
    """Test role-based access control."""

    def test_regular_user_gets_user_role(self, client, user_token):
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "user"

    def test_admin_user_gets_admin_role(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_invalid_token_rejected(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code in (401, 403)


class TestAPIEndpoints:
    """Test critical API endpoints work end-to-end."""

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_register_login_flow(self, client):
        """Test complete registration → login flow."""
        # Register
        resp = client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "password": "StrongPass123!",
            "phone": "+1987654321",
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "newuser@test.com"

        # Login
        resp = client.post("/api/auth/login", json={
            "email": "newuser@test.com",
            "password": "StrongPass123!",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_duplicate_registration_rejected(self, client, user_token):
        """Cannot register with same email twice."""
        resp = client.post("/api/auth/register", json={
            "email": "user@test.com",
            "password": "AnotherPass123!",
            "phone": "+1111111111",
        })
        assert resp.status_code == 400

    def test_leaderboard_public(self, client):
        """Leaderboard should be accessible without auth."""
        resp = client.get("/api/leaderboard/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
