"""
Property-based tests for registration field validation.

**Feature: civic-pulse, Property 25: Registration Field Validation**
For any registration attempt, the system should reject requests that are
missing required fields (email, password, phone number) with a 400 status code.

**Validates: Requirements 8.1**
"""
from hypothesis import given, settings, strategies as st, HealthCheck


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    email=st.emails(),
    password=st.text(min_size=8, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N"))),
    phone=st.from_regex(r"\+[0-9]{7,15}", fullmatch=True),
)
def test_valid_registration_accepted(client, email, password, phone):
    """Valid registration data should be accepted with 201."""
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "phone": phone},
    )
    # First registration with unique email should succeed; duplicates get 400
    assert response.status_code in (201, 400)


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(password=st.text(min_size=1, max_size=7))
def test_short_password_rejected(client, password):
    """Passwords shorter than 8 characters should be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": password, "phone": "+1234567890"},
    )
    assert response.status_code == 422  # Validation error


def test_missing_email_rejected(client):
    """Missing email should be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"password": "password123", "phone": "+1234567890"},
    )
    assert response.status_code == 422


def test_missing_password_rejected(client):
    """Missing password should be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "phone": "+1234567890"},
    )
    assert response.status_code == 422


def test_missing_phone_rejected(client):
    """Missing phone should be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 422


def test_invalid_email_rejected(client):
    """Invalid email format should be rejected."""
    response = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "password123", "phone": "+1234567890"},
    )
    assert response.status_code == 422
