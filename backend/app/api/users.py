"""
User management API endpoints for admins.

Requirements: 8.4, 8.5
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/api/admin/users", tags=["Admin - Users"])


class UserResponse(BaseModel):
    id: str
    email: str
    phone: str
    role: str
    email_verified: bool
    leaderboard_opt_out: bool
    report_count: int
    created_at: str


class UpdateUserRoleRequest(BaseModel):
    role: str


class UpdateUserStatusRequest(BaseModel):
    email_verified: bool


@router.get("/", response_model=List[UserResponse])
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all users with pagination and filtering.
    Admin only.
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) | (User.phone.ilike(f"%{search}%"))
        )
    
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return [
        UserResponse(
            id=str(u.id),
            email=u.email,
            phone=u.phone,
            role=u.role,
            email_verified=u.email_verified,
            leaderboard_opt_out=u.leaderboard_opt_out,
            report_count=u.report_count,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific user.
    Admin only.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        role=user.role,
        email_verified=user.email_verified,
        leaderboard_opt_out=user.leaderboard_opt_out,
        report_count=user.report_count,
        created_at=user.created_at.isoformat(),
    )


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    data: UpdateUserRoleRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update a user's role (user/admin).
    Admin only.
    """
    if data.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'")
    
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from demoting themselves
    if user.id == admin.id and data.role != "admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    
    user.role = data.role
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        role=user.role,
        email_verified=user.email_verified,
        leaderboard_opt_out=user.leaderboard_opt_out,
        report_count=user.report_count,
        created_at=user.created_at.isoformat(),
    )


@router.patch("/{user_id}/verify", response_model=UserResponse)
def verify_user_email(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Manually verify a user's email.
    Admin only.
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.email_verified = True
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        role=user.role,
        email_verified=user.email_verified,
        leaderboard_opt_out=user.leaderboard_opt_out,
        report_count=user.report_count,
        created_at=user.created_at.isoformat(),
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a user account.
    Admin only.
    Requirements: 20.6
    """
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    
    return {"deleted": True, "user_id": user_id}


@router.get("/stats/summary")
def get_user_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get summary statistics about users.
    Admin only.
    """
    total_users = db.query(User).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    verified_users = db.query(User).filter(User.email_verified == True).count()
    
    return {
        "total_users": total_users,
        "admin_users": admin_users,
        "regular_users": total_users - admin_users,
        "verified_users": verified_users,
        "unverified_users": total_users - verified_users,
    }
