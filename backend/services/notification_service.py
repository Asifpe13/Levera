"""In-app notifications + optional push delivery."""
from __future__ import annotations

from typing import Any, Literal

from database.db import DatabaseManager
from services.push_service import PushService

NotificationType = Literal["match", "scan", "weekly", "system"]


class NotificationService:
    def __init__(self, db: DatabaseManager, push: PushService | None = None) -> None:
        self.db = db
        self.push = push or PushService()

    def notify_user(
        self,
        user_email: str,
        *,
        title: str,
        message: str,
        ntype: NotificationType = "system",
        data: dict[str, Any] | None = None,
        send_push: bool = True,
    ) -> dict:
        doc = self.db.create_notification(
            user_email=user_email,
            title=title,
            message=message,
            ntype=ntype,
            data=data,
        )

        if send_push:
            user = self.db.get_user_by_email(user_email) or {}
            if user.get("push_notifications", True):
                tokens = self.db.get_device_tokens(user_email)
                self.push.send_to_tokens(
                    tokens,
                    title=title,
                    body=message,
                    data={
                        "type": ntype,
                        "notification_id": str(doc.get("_id", "")),
                        **{k: str(v) for k, v in (data or {}).items()},
                    },
                )

        return doc
