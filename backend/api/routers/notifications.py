"""In-app notifications for the current user."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.deps import get_current_user_email, get_db
from database.db import DatabaseManager

router = APIRouter()


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: Literal["match", "scan", "weekly", "system"]
    read: bool
    created_at: str
    data: dict = Field(default_factory=dict)


class MarkNotificationsRequest(BaseModel):
    ids: Optional[list[str]] = None
    mark_all: bool = False
    read: bool = True


def _serialize(doc: dict) -> NotificationResponse:
    return NotificationResponse(
        id=str(doc["_id"]),
        title=doc.get("title", ""),
        message=doc.get("message", ""),
        type=doc.get("type", "system"),
        read=bool(doc.get("read", False)),
        created_at=doc.get("created_at").isoformat()
        if hasattr(doc.get("created_at"), "isoformat")
        else str(doc.get("created_at", "")),
        data=doc.get("data") or {},
    )


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
    unread_only: bool = Query(False),
    limit: int = Query(50, le=200),
):
    docs = db.list_notifications(email, unread_only=unread_only, limit=limit)
    return [_serialize(d) for d in docs]


@router.patch("/read")
def mark_notifications_read(
    body: MarkNotificationsRequest,
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    if body.mark_all:
        count = db.mark_all_notifications(email, read=body.read)
        return {"updated": count}

    if not body.ids:
        raise HTTPException(status_code=400, detail="ids or mark_all required")

    count = db.mark_notifications(email, body.ids, read=body.read)
    return {"updated": count}


@router.delete("/read")
def delete_read_notifications(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    count = db.delete_read_notifications(email)
    return {"deleted": count}
