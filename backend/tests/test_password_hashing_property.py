"""
Property-based tests for password hashing.

**Feature: civic-pulse, Property 26: Password Hashing**
For any user registration or password change, the system should never store 
plaintext passwords; all passwords should be hashed using bcrypt before storage.

**Validates: Requirements 8.3**
"""
import pytest
from hypothesis import given, settings, strategies as st
from app.models.user import User


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "P"))))
def test_password_never_stored_plaintext(password):
    """
    Property 26: Password Hashing
    
    For any password string, the system should:
    1. Never store the password in plaintext
    2. Hash the password using bcrypt
    3. Be able to verify the original password against the hash
    4. Reject incorrect passwords
    
    Validates: Requirements 8.3
    """
    user = User(
        email="test@example.com",
        phone="+1234567890"
    )
    user.set_password(password)
    
    assert user.password_hash != password, \
        "Password hash must not be the same as plaintext password"
    
    assert user.password_hash is not None, \
        "Password hash must not be None"
    assert len(user.password_hash) > 0, \
        "Password hash must not be empty"
    
    assert user.password_hash.startswith('$2b$'), \
        "Password hash must be a valid bcrypt hash (starting with $2b$)"
    
    assert user.check_password(password) is True, \
        "Original password must verify successfully against the hash"
    
    # Use a clearly different password to avoid bcrypt 72-byte truncation edge cases
    wrong_password = "WRONG_" + password[:20] + "_WRONG"
    if wrong_password != password:
        assert user.check_password(wrong_password) is False, \
            "Modified password must not verify against the hash"


@settings(max_examples=20, deadline=None)
@given(
    password1=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))),
    password2=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N")))
)
def test_different_passwords_produce_different_hashes(password1, password2):
    """
    Property: Different passwords should produce different hashes.
    
    Even if two passwords are similar, their bcrypt hashes should be different
    due to the salt used in bcrypt.
    
    Validates: Requirements 8.3
    """
    # Skip if passwords are identical
    if password1 == password2:
        return
    
    user1 = User(email="user1@example.com", phone="+1111111111")
    user1.set_password(password1)
    
    user2 = User(email="user2@example.com", phone="+2222222222")
    user2.set_password(password2)
    
    # Different passwords should produce different hashes
    assert user1.password_hash != user2.password_hash, \
        "Different passwords must produce different hashes"


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))))
def test_same_password_produces_different_hashes_with_salt(password):
    """
    Property: Same password should produce different hashes due to salt.
    
    Bcrypt uses a random salt for each hash, so the same password should
    produce different hashes when set multiple times.
    
    Validates: Requirements 8.3
    """
    user1 = User(email="user1@example.com", phone="+1111111111")
    user1.set_password(password)
    
    user2 = User(email="user2@example.com", phone="+2222222222")
    user2.set_password(password)
    
    # Same password should produce different hashes due to different salts
    assert user1.password_hash != user2.password_hash, \
        "Same password must produce different hashes due to bcrypt salt"
    
    # But both should verify the same password
    assert user1.check_password(password) is True
    assert user2.check_password(password) is True


@settings(max_examples=20, deadline=None)
@given(
    password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))),
    email=st.emails(),
    phone=st.text(min_size=1, max_size=20)
)
def test_password_hashing_with_various_user_data(password, email, phone):
    """
    Property: Password hashing should work correctly regardless of user data.
    
    The password hashing mechanism should be independent of other user
    attributes like email and phone number.
    
    Validates: Requirements 8.3
    """
    user = User(email=email, phone=phone)
    user.set_password(password)
    
    # Password should be hashed
    assert user.password_hash != password
    assert user.password_hash.startswith('$2b$')
    
    # Password verification should work
    assert user.check_password(password) is True
    
    # User data should not affect password verification
    assert user.email == email
    assert user.phone == phone


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))))
def test_password_change_updates_hash(password):
    """
    Property: Changing a password should update the hash.
    
    When a user changes their password, the old hash should be replaced
    with a new hash, and only the new password should verify.
    
    Validates: Requirements 8.3
    """
    user = User(email="test@example.com", phone="+1234567890")
    
    # Set initial password
    initial_password = "initial_password_123"
    user.set_password(initial_password)
    initial_hash = user.password_hash
    
    # Change to new password
    user.set_password(password)
    new_hash = user.password_hash
    
    # Hash should have changed (unless passwords are identical)
    if password != initial_password:
        assert new_hash != initial_hash, \
            "Password hash must change when password is changed"
    
    # New password should verify
    assert user.check_password(password) is True
    
    # Old password should not verify (unless passwords are identical)
    if password != initial_password:
        assert user.check_password(initial_password) is False, \
            "Old password must not verify after password change"


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))))
def test_password_verification_is_deterministic(password):
    """
    Property: Password verification should be deterministic.
    
    Verifying the same password multiple times should always return the
    same result (True for correct password, False for incorrect).
    
    Validates: Requirements 8.3
    """
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password(password)
    
    # Verify the correct password multiple times
    for _ in range(5):
        assert user.check_password(password) is True, \
            "Password verification must be deterministic for correct password"
    
    # Verify an incorrect password multiple times
    wrong_password = password + "_wrong"
    for _ in range(5):
        assert user.check_password(wrong_password) is False, \
            "Password verification must be deterministic for incorrect password"


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N", "P"))))
def test_password_hashing_with_special_characters(password):
    """
    Property: Password hashing should handle special characters correctly.
    
    Passwords with special characters, unicode, spaces, etc. should all
    be hashed and verified correctly.
    
    Validates: Requirements 8.3
    """
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password(password)
    
    # Password should be hashed
    assert user.password_hash != password
    assert user.password_hash.startswith('$2b$')
    
    # Password verification should work with special characters
    assert user.check_password(password) is True


@settings(max_examples=20, deadline=None)
@given(password=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))))
def test_password_hash_length_is_consistent(password):
    """
    Property: Bcrypt hashes should have consistent length.
    
    All bcrypt hashes should be 60 characters long, regardless of the
    input password length.
    
    Validates: Requirements 8.3
    """
    user = User(email="test@example.com", phone="+1234567890")
    user.set_password(password)
    
    # Bcrypt hashes are always 60 characters
    assert len(user.password_hash) == 60, \
        "Bcrypt hash must be exactly 60 characters long"
