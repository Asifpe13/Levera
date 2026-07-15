"""
Push notification delivery — FCM HTTP v1 and Expo Push API.

When credentials are not configured (typical local dev), calls are logged and skipped
so the rest of the app (in-app notifications, device token storage) still works.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from loguru import logger


class PushService:
    def __init__(self) -> None:
        self._fcm_project_id = os.getenv("FCM_PROJECT_ID", "").strip()
        self._fcm_service_account_json = os.getenv("FCM_SERVICE_ACCOUNT_JSON", "").strip()
        self._expo_access_token = os.getenv("EXPO_ACCESS_TOKEN", "").strip()
        self._fcm_access_token: str | None = None

    def _fcm_enabled(self) -> bool:
        return bool(self._fcm_project_id and self._fcm_service_account_json)

    def _expo_enabled(self) -> bool:
        return bool(self._expo_access_token)

    def _get_fcm_access_token(self) -> str | None:
        if self._fcm_access_token:
            return self._fcm_access_token
        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests

            info = json.loads(self._fcm_service_account_json)
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            creds.refresh(google.auth.transport.requests.Request())
            self._fcm_access_token = creds.token
            return self._fcm_access_token
        except Exception as exc:
            logger.warning(f"FCM auth unavailable: {exc}")
            return None

    def send_to_tokens(
        self,
        tokens: list[dict[str, Any]],
        *,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> None:
        if not tokens:
            return

        payload_data = {k: str(v) for k, v in (data or {}).items()}

        expo_tokens = [t["token"] for t in tokens if t.get("platform") == "expo"]
        fcm_tokens = [
            t["token"]
            for t in tokens
            if t.get("platform") in ("android", "ios", "web")
        ]

        if expo_tokens:
            self._send_expo(expo_tokens, title, body, payload_data)
        if fcm_tokens:
            self._send_fcm(fcm_tokens, title, body, payload_data)

        if not expo_tokens and not fcm_tokens:
            logger.debug(f"Push skipped (no known platform tokens): {title}")

    def _send_expo(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str],
    ) -> None:
        if not self._expo_enabled():
            logger.info(f"[push/expo] skipped (no EXPO_ACCESS_TOKEN): {title}")
            return

        messages = [
            {
                "to": token,
                "title": title,
                "body": body,
                "data": data,
                "sound": "default",
            }
            for token in tokens
        ]
        try:
            resp = httpx.post(
                "https://exp.host/--/api/v2/push/send",
                json=messages,
                headers={
                    "Authorization": f"Bearer {self._expo_access_token}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            logger.info(f"[push/expo] sent '{title}' to {len(tokens)} device(s)")
        except Exception as exc:
            logger.warning(f"[push/expo] failed: {exc}")

    def _send_fcm(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str],
    ) -> None:
        if not self._fcm_enabled():
            logger.info(f"[push/fcm] skipped (no FCM credentials): {title}")
            return

        access_token = self._get_fcm_access_token()
        if not access_token:
            return

        url = f"https://fcm.googleapis.com/v1/projects/{self._fcm_project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        for token in tokens:
            message = {
                "message": {
                    "token": token,
                    "notification": {"title": title, "body": body},
                    "data": data,
                }
            }
            try:
                resp = httpx.post(url, json=message, headers=headers, timeout=15)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning(f"[push/fcm] token failed: {exc}")

        logger.info(f"[push/fcm] sent '{title}' to {len(tokens)} device(s)")
