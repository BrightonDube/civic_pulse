"""
Property-based tests for password reset token expiration.

**Feature: civic-pulse, Property 28: Password Reset Token Expiration**
For any password reset token, the token should be valid for a limited time
period (e.g., 1 hour), and attempts to use expired tokens should be rejected.

**Validates: Requirements 8.7**
"""
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from hypothesis import given, settings as h_settings, strategies as st
from jose import jwt

from app.services.auth_service import (
    AuthService,
    create_reset_token,
    decode_token,
    ALGORITHM,
)
from app.core.config import settings


def test_reset_token_valid_within_expiry(db_session):
    """A fresh reset token should be valid."""
    service = AuthService(db_session)
    service.register_user("test@example.com", "oldpass123", "+1234567890")

    token = service.request_password_reset("test@example.com")
    assert token is not None

    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["type"] == "reset"


def test_expired_reset_token_rejected(db_session):
    """An expired reset token should be rejected."""
    # Create a token that expired 1 second ago
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    data = {"sub": "test@example.com", "type": "reset", "exp": expire}
    expired_token = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)

    service = AuthService(db_session)
    service.register_user("test@example.com", "oldpass123", "+1234567890")

    success = service.reset_password(expired_token, "newpass123")
    assert success is False


def test_reset_token_wrong_type_rejected(db_session):
    """A token without type='reset' should be rejected for password reset."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    data = {"sub": "test@example.com", "type": "access", "exp": expire}
    wrong_token = jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)

    service = AuthService(db_session)
    service.register_user("test@example.com", "oldpass123", "+1234567890")

    success = service.reset_password(wrong_token, "newpass123")
    assert success is False


@h_settings(max_examples=20)
@given(email=st.emails())
def test_reset_token_contains_email(email):
    """Reset token should contain the email in the payload."""
    token = create_reset_token(email)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == email
    assert payload["type"] == "reset"
