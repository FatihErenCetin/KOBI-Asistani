from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_webhook_requires_secret(client):
    r = client.post("/api/v1/webhooks/telegram", json={"update_id": 1})
    assert r.status_code == 401


def test_webhook_accepts_valid_secret(client):
    headers = {"x-telegram-bot-api-secret-token": settings.TELEGRAM_WEBHOOK_SECRET}
    r = client.post(
        "/api/v1/webhooks/telegram",
        json={"update_id": 1},
        headers=headers,
    )
    assert r.status_code == 200


def test_webhook_handles_contact_share(client):
    headers = {"x-telegram-bot-api-secret-token": settings.TELEGRAM_WEBHOOK_SECRET}
    payload = {
        "update_id": 2,
        "message": {
            "message_id": 1,
            "from": {"id": 999, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 999},
            "date": 1700000000,
            "contact": {"phone_number": "+905551112233", "first_name": "Test"},
        },
    }
    with patch("app.api.v1.webhooks._process_contact", new=AsyncMock()):
        r = client.post("/api/v1/webhooks/telegram", json=payload, headers=headers)
    assert r.status_code == 200
