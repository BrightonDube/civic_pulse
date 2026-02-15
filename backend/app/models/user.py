import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import bcrypt
from app.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's UUID type when available, otherwise CHAR(36)."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name == "postgresql":
                return str(value)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(str(value))
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))


class User(Base):
    """
    User model for authentication and authorization.
    
    Supports both regular users and admins with role-based access control.
    Implements secure password hashing with bcrypt.
    
    Requirements: 8.1, 8.3
    """
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")  # "user" or "admin"
    email_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    leaderboard_opt_out = Column(Boolean, nullable=False, default=False)
    report_count = Column(Integer, nullable=False, default=0)

    def __init__(self, **kwargs):
        """Initialize User with default values for optional fields."""
        # Set defaults for fields not provided
        kwargs.setdefault('role', 'user')
        kwargs.setdefault('email_verified', False)
        kwargs.setdefault('leaderboard_opt_out', False)
        kwargs.setdefault('report_count', 0)
        super().__init__(**kwargs)

    def set_password(self, password: str) -> None:
        """
        Hash and store a password using bcrypt.
        
        Args:
            password: Plain text password to hash
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
