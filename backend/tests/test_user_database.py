"""
Database integration tests for User model.

These tests verify that the User model works correctly with the database,
including unique constraints and password hashing.

Requirements: 8.1, 8.3
"""
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User


def test_user_database_creation(db_session):
    """Test that a User can be created and persisted to the database."""
    user = User(
        email="test@example.com",
        phone="+1234567890",
        role="user"
    )
    user.set_password("secure_password")
    
    db_session.add(user)
    db_session.commit()
    
    # Retrieve the user from the database
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.phone == "+1234567890"
    assert retrieved_user.role == "user"
    assert retrieved_user.check_password("secure_password") is True


def test_email_unique_constraint(db_session):
    """Test that the unique constraint on email is enforced."""
    user1 = User(
        email="duplicate@example.com",
        phone="+1234567890"
    )
    user1.set_password("password1")
    
    user2 = User(
        email="duplicate@example.com",
        phone="+0987654321"
    )
    user2.set_password("password2")
    
    db_session.add(user1)
    db_session.commit()
    
    # Attempting to add a second user with the same email should fail
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_multiple_users_different_emails(db_session):
    """Test that multiple users with different emails can be created."""
    user1 = User(email="user1@example.com", phone="+1111111111")
    user1.set_password("password1")
    
    user2 = User(email="user2@example.com", phone="+2222222222")
    user2.set_password("password2")
    
    user3 = User(email="user3@example.com", phone="+3333333333")
    user3.set_password("password3")
    
    db_session.add_all([user1, user2, user3])
    db_session.commit()
    
    # All users should be retrievable
    users = db_session.query(User).all()
    assert len(users) == 3
    
    emails = {user.email for user in users}
    assert emails == {"user1@example.com", "user2@example.com", "user3@example.com"}


def test_password_persistence(db_session):
    """Test that password hashes are correctly persisted and retrieved."""
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password("my_password")
    
    db_session.add(user)
    db_session.commit()
    
    # Clear the session to force a fresh database query
    db_session.expunge_all()
    
    # Retrieve the user and verify password
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user.check_password("my_password") is True
    assert retrieved_user.check_password("wrong_password") is False


def test_user_role_persistence(db_session):
    """Test that user roles are correctly persisted."""
    regular_user = User(email="user@example.com", phone="+1111111111", role="user")
    regular_user.set_password("password")
    
    admin_user = User(email="admin@example.com", phone="+2222222222", role="admin")
    admin_user.set_password("password")
    
    db_session.add_all([regular_user, admin_user])
    db_session.commit()
    
    # Retrieve and verify roles
    retrieved_user = db_session.query(User).filter_by(email="user@example.com").first()
    retrieved_admin = db_session.query(User).filter_by(email="admin@example.com").first()
    
    assert retrieved_user.role == "user"
    assert retrieved_admin.role == "admin"


def test_email_verified_flag_persistence(db_session):
    """Test that email_verified flag is correctly persisted."""
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password("password")
    user.email_verified = True
    
    db_session.add(user)
    db_session.commit()
    
    # Retrieve and verify
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user.email_verified is True


def test_report_count_persistence(db_session):
    """Test that report_count is correctly persisted and can be updated."""
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password("password")
    user.report_count = 5
    
    db_session.add(user)
    db_session.commit()
    
    # Retrieve and verify
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved_user.report_count == 5
    
    # Update and verify again
    retrieved_user.report_count += 1
    db_session.commit()
    
    db_session.expunge_all()
    updated_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert updated_user.report_count == 6
