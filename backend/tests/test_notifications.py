"""Tests for notifications API."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.deps import get_db, get_current_user_email


@pytest.fixture
def client():
    mock_db = MagicMock()
    mock_db.get_user_by_email.return_value = {
        "email": "test@example.com",
        "name": "Test",
        "target_cities": ["תל אביב - יפו"],
        "search_type": "buy",
        "profile_type": "HOME_BUYER",
        "home_index": 1,
        "loan_term_years": 30,
        "equity": 300000,
        "monthly_income": 20000,
        "room_range_min": 3,
        "room_range_max": 5,
        "max_price": 1500000,
        "max_repayment_ratio": 0.4,
        "rent_room_range_min": 2,
        "rent_room_range_max": 4,
        "max_rent": None,
        "extra_preferences": None,
        "email_notifications": True,
        "push_notifications": True,
    }
    mock_db.list_notifications.return_value = [
        {
            "_id": "abc123",
            "title": "בדיקה",
            "message": "הודעת בדיקה",
            "type": "system",
            "read": False,
            "created_at": datetime.now(timezone.utc),
            "data": {},
        }
    ]
    mock_db.mark_all_notifications.return_value = 1
    mock_db.upsert_device_token.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user_email] = lambda: "test@example.com"

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_list_notifications(client):
    res = client.get("/notifications", headers={"Authorization": "Bearer fake"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "בדיקה"


def test_register_device_token(client):
    res = client.post(
        "/user/device-token",
        json={"token": "ExponentPushToken[test]", "platform": "expo"},
        headers={"Authorization": "Bearer fake"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
