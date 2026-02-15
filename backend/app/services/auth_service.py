"""
Authentication service for user registration, login, and JWT management.

Requirements: 8.1, 8.2, 8.3, 8.6, 8.7
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
RESET_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(email: str) -> str:
    """Create a time-limited password reset token. Requirements: 8.7"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    data = {"sub": email, "type": "reset", "exp": expire}
    return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class AuthService:
    """Service for user authentication operations."""

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, email: str, password: str, phone: str) -> User:
        """
        Register a new user.
        Requirements: 8.1, 8.3
        """
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")

        user = User(email=email, phone=phone)
        user.set_password(password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, email: str, password: str) -> Optional[str]:
        """
        Authenticate user and return JWT token.
        Requirements: 8.3, 8.6
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.check_password(password):
            return None

        token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )
        return token

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            return None
        return self.db.query(User).filter(User.id == uid).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def request_password_reset(self, email: str) -> Optional[str]:
        """
        Generate a password reset token if the user exists.
        Requirements: 8.7
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        return create_reset_token(email)

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using a valid reset token.
        Requirements: 8.7
        """
        payload = decode_token(token)
        if not payload or payload.get("type") != "reset":
            return False

        email = payload.get("sub")
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return False

        user.set_password(new_password)
        self.db.commit()
        return True
