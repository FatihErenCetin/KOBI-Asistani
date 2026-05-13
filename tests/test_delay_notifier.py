"""Proaktif gecikme bildirimi — risk scanner side effect testleri."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import (
    OrderStatus,
    Product,
    Shipment,
    ShipmentStatus,
)
from app.services import proactive_risk_scanner


@pytest.mark.asyncio
async def test_notification_skipped_when_flag_off(db):
    """PROACTIVE_NOTIFICATIONS_ENABLED=False ise hiçbir Telegram çağrısı olmaz."""
    finding = {"customer_id": 1, "order_id": 42, "days_overdue": 3, "current_location": "Ankara"}

    with patch.object(
        proactive_risk_scanner.settings, "PROACTIVE_NOTIFICATIONS_ENABLED", False
    ):
        # SessionLocal'ı bile import etmemeli — exit erken
        await proactive_risk_scanner._notify_delay_to_customer(finding)
        await proactive_risk_scanner._notify_delay_to_admin(finding)


@pytest.mark.asyncio
async def test_notify_customer_with_telegram_id():
    """Müşterinin tg_id'si finding'de varsa Telegram mesajı gönderilir."""
    finding = {
        "customer_id": 1,
        "customer_name": "Test Müşteri",
        "telegram_user_id": 12345,
        "order_id": 99,
        "days_overdue": 2,
        "current_location": "İstanbul",
    }

    send_mock = AsyncMock()
    with patch.object(
        proactive_risk_scanner.settings, "PROACTIVE_NOTIFICATIONS_ENABLED", True
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        await proactive_risk_scanner._notify_delay_to_customer(finding)

    send_mock.assert_awaited_once()
    args, _ = send_mock.call_args
    assert args[0] == 12345  # chat_id
    assert "#99" in args[1]
    assert "2 gün" in args[1]


@pytest.mark.asyncio
async def test_notify_customer_skips_when_no_telegram():
    """Müşterinin tg_id'si finding'de yoksa atlama."""
    finding = {
        "customer_id": 5,
        "customer_name": "Test",
        "telegram_user_id": None,
        "order_id": 1,
        "days_overdue": 1,
        "current_location": None,
    }

    send_mock = AsyncMock()
    with patch.object(
        proactive_risk_scanner.settings, "PROACTIVE_NOTIFICATIONS_ENABLED", True
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        await proactive_risk_scanner._notify_delay_to_customer(finding)

    send_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_admin_requires_admin_telegram_id():
    """ADMIN_TELEGRAM_ID boşsa admin notify gönderilmez."""
    send_mock = AsyncMock()
    with patch.object(
        proactive_risk_scanner.settings, "PROACTIVE_NOTIFICATIONS_ENABLED", True
    ), patch.object(
        proactive_risk_scanner.settings, "ADMIN_TELEGRAM_ID", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        await proactive_risk_scanner._notify_delay_to_admin(
            {"order_id": 1, "tracking_no": "TR", "carrier": "x",
             "customer_name": "Y", "days_overdue": 3, "current_location": "z"}
        )
    send_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_scan_triggers_notification_for_delay(db):
    """End-to-end: scan_and_report bir delay bulgu için bildirim çağırır."""
    c = await customers_crud.create(
        db, name="X", telegram_user_id=77777
    )
    p = Product(name="P", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    o.status = OrderStatus.SHIPPED
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-DELAY-NOTIF",
        carrier="MockKargo",
        status=ShipmentStatus.IN_TRANSIT,
        estimated_delivery=date.today() - timedelta(days=3),
        last_event_at=datetime.utcnow() - timedelta(days=5),
        current_location="Ankara Aktarma",
    )
    db.add(s)
    await db.flush()

    send_mock = AsyncMock()
    with patch.object(
        proactive_risk_scanner.settings, "PROACTIVE_NOTIFICATIONS_ENABLED", True
    ), patch.object(
        proactive_risk_scanner, "_llm_narrate",
        new=AsyncMock(return_value=("Geç kaldı", "açıklama")),
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        result = await proactive_risk_scanner.scan_and_report(db)

    assert result["shipment_delay"] >= 1
    # En az müşteriye 1 mesaj gönderilmeli
    assert send_mock.await_count >= 1
