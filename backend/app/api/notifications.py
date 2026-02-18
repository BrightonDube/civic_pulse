"""
Notification API endpoints.

Requirements: 4.3, 17.2, 17.3
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    report_id: str | None
    type: str
    title: str
    message: str
    read: bool
    created_at: str


class MarkReadRequest(BaseModel):
    notification_ids: List[str]


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all notifications for the current user in reverse chronological order.
    Requirements: 17.2, 17.3
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    
    return [
        NotificationResponse(
            id=str(n.id),
            user_id=str(n.user_id),
            report_id=str(n.report_id) if n.report_id else None,
            type=n.type,
            title=n.title,
            message=n.message,
            read=n.read,
            created_at=n.created_at.isoformat(),
        )
        for n in notifications
    ]


@router.get("/unread/count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get count of unread notifications for the current user."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.read == False)
        .count()
    )
    return {"count": count}


@router.post("/mark-read")
def mark_notifications_read(
    data: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark notifications as read."""
    notification_uuids = []
    for nid in data.notification_ids:
        try:
            notification_uuids.append(uuid.UUID(nid))
        except ValueError:
            continue
    
    if not notification_uuids:
        return {"updated": 0}
    
    updated = (
        db.query(Notification)
        .filter(
            Notification.id.in_(notification_uuids),
            Notification.user_id == current_user.id
        )
        .update({"read": True}, synchronize_session=False)
    )
    db.commit()
    
    return {"updated": updated}


@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.read == False)
        .update({"read": True}, synchronize_session=False)
    )
    db.commit()
    
    return {"updated": updated}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    try:
        nid = uuid.UUID(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notification = (
        db.query(Notification)
        .filter(Notification.id == nid, Notification.user_id == current_user.id)
        .first()
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"deleted": True}
