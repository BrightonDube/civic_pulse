"""Pydantic schemas for authentication."""
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    """Schema for user registration. Requirements: 8.1"""
    email: EmailStr
    password: str
    phone: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^\+?[0-9]{7,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: str
    email: str
    phone: str
    role: str
    email_verified: bool
    report_count: int
    leaderboard_opt_out: bool

    model_config = {"from_attributes": True}


class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming a password reset."""
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
