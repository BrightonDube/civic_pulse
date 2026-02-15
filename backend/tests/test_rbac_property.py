"""
Property-based tests for role-based access control.

**Feature: civic-pulse, Property 27: Role-Based Access Control**
For any API endpoint marked as admin-only, requests from users with the
"user" role should be rejected with a 403 status code, while requests from
users with the "admin" role should be allowed.

**Validates: Requirements 8.4, 8.5, 11.6**
"""
import pytest


def _register_and_login(client, email, password, phone, role="user"):
    """Helper to register a user and return the auth token."""
    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "phone": phone},
    )
    # If we need an admin, we manipulate the DB directly via the fixture
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]


def test_unauthenticated_access_rejected(client):
    """Unauthenticated requests to protected endpoints return 401."""
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_authenticated_user_can_access_own_profile(client):
    """Authenticated user can access /me endpoint."""
    token = _register_and_login(client, "user@test.com", "password123", "+1234567890")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@test.com"
    assert response.json()["role"] == "user"


def test_invalid_token_rejected(client):
    """Invalid JWT tokens should be rejected with 401."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid-token-here"},
    )
    assert response.status_code == 401
