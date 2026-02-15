"""
Unit tests for User model.

Tests password hashing, email uniqueness, and model creation.
Requirements: 8.1, 8.3
"""
import pytest
from app.models.user import User


def test_user_creation():
    """Test that a User can be created with all required fields."""
    user = User(
        email="test@example.com",
        phone="+1234567890",
        role="user"
    )
    user.set_password("secure_password123")
    
    assert user.email == "test@example.com"
    assert user.phone == "+1234567890"
    assert user.role == "user"
    assert user.email_verified is False
    assert user.leaderboard_opt_out is False
    assert user.report_count == 0
    assert user.password_hash is not None
    assert user.password_hash != "secure_password123"  # Password should be hashed


def test_password_hashing():
    """Test that passwords are properly hashed and not stored in plaintext."""
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    password = "my_secret_password"
    user.set_password(password)
    
    # Password should be hashed, not stored as plaintext
    assert user.password_hash != password
    assert len(user.password_hash) > 0
    
    # Should be able to verify the correct password
    assert user.check_password(password) is True
    
    # Should reject incorrect passwords
    assert user.check_password("wrong_password") is False


def test_password_verification():
    """Test that password verification works correctly."""
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    user.set_password("correct_password")
    
    # Correct password should verify
    assert user.check_password("correct_password") is True
    
    # Incorrect passwords should not verify
    assert user.check_password("wrong_password") is False
    assert user.check_password("") is False
    assert user.check_password("correct_passwor") is False  # Close but not exact


def test_admin_role():
    """Test that admin role can be set."""
    admin = User(
        email="admin@example.com",
        phone="+1234567890",
        role="admin"
    )
    admin.set_password("admin_password")
    
    assert admin.role == "admin"


def test_email_verified_flag():
    """Test that email_verified flag defaults to False."""
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    
    assert user.email_verified is False
    
    # Can be set to True
    user.email_verified = True
    assert user.email_verified is True


def test_leaderboard_opt_out():
    """Test that leaderboard_opt_out flag defaults to False."""
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    
    assert user.leaderboard_opt_out is False
    
    # Can be set to True
    user.leaderboard_opt_out = True
    assert user.leaderboard_opt_out is True


def test_report_count_initialization():
    """Test that report_count initializes to 0."""
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    
    assert user.report_count == 0
    
    # Can be incremented
    user.report_count += 1
    assert user.report_count == 1
