"""
Tests for AuthService - registration, login, JWT, and password reset.

Requirements: 8.1, 8.3, 8.6, 8.7
"""
import time
import pytest
from app.services.auth_service import AuthService, create_access_token, decode_token, create_reset_token


def test_register_user(db_session):
    """Test successful user registration."""
    service = AuthService(db_session)
    user = service.register_user("test@example.com", "password123", "+1234567890")

    assert user.email == "test@example.com"
    assert user.phone == "+1234567890"
    assert user.role == "user"
    assert user.check_password("password123")


def test_register_duplicate_email(db_session):
    """Test that duplicate email registration raises ValueError."""
    service = AuthService(db_session)
    service.register_user("test@example.com", "password123", "+1234567890")

    with pytest.raises(ValueError, match="Email already registered"):
        service.register_user("test@example.com", "password456", "+0987654321")


def test_login_success(db_session):
    """Test successful login returns JWT token."""
    service = AuthService(db_session)
    service.register_user("test@example.com", "password123", "+1234567890")

    token = service.login("test@example.com", "password123")
    assert token is not None

    payload = decode_token(token)
    assert payload is not None
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"


def test_login_wrong_password(db_session):
    """Test login with wrong password returns None."""
    service = AuthService(db_session)
    service.register_user("test@example.com", "password123", "+1234567890")

    token = service.login("test@example.com", "wrongpassword")
    assert token is None


def test_login_nonexistent_user(db_session):
    """Test login with nonexistent email returns None."""
    service = AuthService(db_session)
    token = service.login("nobody@example.com", "password123")
    assert token is None


def test_token_creation_and_decoding():
    """Test JWT token creation and decoding."""
    data = {"sub": "user-id-123", "email": "test@example.com", "role": "user"}
    token = create_access_token(data)
    payload = decode_token(token)

    assert payload is not None
    assert payload["sub"] == "user-id-123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"


def test_decode_invalid_token():
    """Test that invalid tokens return None."""
    assert decode_token("invalid-token") is None
    assert decode_token("") is None


def test_password_reset_flow(db_session):
    """Test complete password reset flow. Requirements: 8.7"""
    service = AuthService(db_session)
    service.register_user("test@example.com", "oldpassword", "+1234567890")

    # Request reset token
    token = service.request_password_reset("test@example.com")
    assert token is not None

    # Reset password
    success = service.reset_password(token, "newpassword123")
    assert success is True

    # Login with new password
    login_token = service.login("test@example.com", "newpassword123")
    assert login_token is not None

    # Old password should no longer work
    assert service.login("test@example.com", "oldpassword") is None


def test_password_reset_nonexistent_email(db_session):
    """Test password reset for nonexistent email returns None."""
    service = AuthService(db_session)
    token = service.request_password_reset("nobody@example.com")
    assert token is None


def test_password_reset_invalid_token(db_session):
    """Test password reset with invalid token fails."""
    service = AuthService(db_session)
    success = service.reset_password("invalid-token", "newpassword")
    assert success is False
