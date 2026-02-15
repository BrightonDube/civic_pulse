"""
Authentication API endpoints.

Requirements: 8.1, 8.3, 8.6, 8.7, 11.2
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    MessageResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user. Requirements: 8.1"""
    service = AuthService(db)
    try:
        user = service.register_user(data.email, data.password, data.phone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        role=user.role,
        email_verified=user.email_verified,
        report_count=user.report_count,
        leaderboard_opt_out=user.leaderboard_opt_out,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login and receive JWT token. Requirements: 8.3, 8.6"""
    service = AuthService(db)
    token = service.login(data.email, data.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile. Requirements: 8.6"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        email_verified=current_user.email_verified,
        report_count=current_user.report_count,
        leaderboard_opt_out=current_user.leaderboard_opt_out,
    )


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset link. Requirements: 8.7"""
    service = AuthService(db)
    # Always return success to prevent email enumeration
    service.request_password_reset(data.email)
    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password with token. Requirements: 8.7"""
    service = AuthService(db)
    success = service.reset_password(data.token, data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return MessageResponse(message="Password reset successfully")
