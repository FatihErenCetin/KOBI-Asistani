"""Kargo durum bildirimi servisi testleri.

AI yokken fallback template kullanmali, status -> ozel mesaj eslesmesi,
telegram_user_id yoksa atlama, flag kapaliysa atlama.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Product, Shipment, ShipmentStatus
from app.services import shipment_notifier


async def _make_shipment_with_customer(
    db,
    *,
    customer_name="Ayse",
    telegram_user_id=99001,
    product_name="Bal",
    status=ShipmentStatus.LABEL_CREATED,
):
    customer = await customers_crud.create(
        db, name=customer_name, telegram_user_id=telegram_user_id
    )
    product = Product(name=product_name, unit="kg", price=100, cost=60)
    db.add(product)
    await db.flush()
    order = await orders_crud.create_order(
        db, customer_id=customer.id, items=[(product, 2)]
    )
    shipment = Shipment(
        order_id=order.id,
        tracking_no="TR-NOTIFY-TEST",
        carrier="MockKargo",
        status=status,
        estimated_delivery=date.today() + timedelta(days=2),
        last_event_at=datetime.utcnow(),
        current_location="Ankara Aktarma",
    )
    db.add(shipment)
    await db.flush()
    return customer, order, shipment


@pytest.mark.asyncio
async def test_notify_skipped_when_flag_disabled(db):
    _, _, shipment = await _make_shipment_with_customer(db)
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        False,
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        result = await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.PICKED_UP
        )
    assert result is False
    send_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_skipped_without_telegram_id(db):
    _, _, shipment = await _make_shipment_with_customer(
        db, telegram_user_id=None
    )
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        result = await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.PICKED_UP
        )
    assert result is False
    send_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_label_created_not_notifiable(db):
    """LABEL_CREATED durumu fiziksel teslim aşaması değil — bildirim yok."""
    _, _, shipment = await _make_shipment_with_customer(db)
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        result = await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.LABEL_CREATED
        )
    assert result is False
    send_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_picked_up_uses_fallback_template_without_llm(db):
    """Gemini yoksa template fallback çalışmalı; mesajda ad + sipariş no olmalı."""
    _, order, shipment = await _make_shipment_with_customer(db)
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEY", ""
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEYS", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        result = await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.PICKED_UP
        )

    assert result is True
    send_mock.assert_awaited_once()
    args, kwargs = send_mock.call_args
    assert args[0] == 99001  # tg_id
    body = args[1]
    assert "Ayse" in body
    assert f"#{order.id}" in body
    assert "kargo" in body.lower()


@pytest.mark.asyncio
async def test_notify_delivered_uses_thank_you_template(db):
    _, _, shipment = await _make_shipment_with_customer(db)
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEY", ""
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEYS", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.DELIVERED
        )

    body = send_mock.call_args.args[1]
    assert "teslim" in body.lower() or "Teslim" in body
    assert "teşekkür" in body.lower() or "teşekkur" in body.lower()


@pytest.mark.asyncio
async def test_notify_in_transit_includes_location(db):
    _, _, shipment = await _make_shipment_with_customer(db)
    shipment.current_location = "İstanbul Anadolu Şubesi"
    await db.flush()
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEY", ""
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEYS", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.IN_TRANSIT
        )

    body = send_mock.call_args.args[1]
    assert "İstanbul" in body


@pytest.mark.asyncio
async def test_notify_telegram_failure_returns_false(db):
    """Telegram API hata atarsa False döner, exception caller'a sızmaz."""
    _, _, shipment = await _make_shipment_with_customer(db)
    failing_send = AsyncMock(side_effect=RuntimeError("network down"))
    with patch.object(
        shipment_notifier.settings,
        "SHIPMENT_NOTIFICATIONS_ENABLED",
        True,
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEY", ""
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEYS", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=failing_send,
    ):
        result = await shipment_notifier.notify_status_change(
            db, shipment, ShipmentStatus.PICKED_UP
        )
    assert result is False


@pytest.mark.asyncio
async def test_notify_delay_uses_fallback_when_llm_unavailable(db):
    """notify_delay LLM yoksa template kullanır; mesajda 'özür' geçer."""
    send_mock = AsyncMock()
    with patch.object(
        shipment_notifier.settings,
        "PROACTIVE_NOTIFICATIONS_ENABLED",
        True,
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEY", ""
    ), patch.object(
        shipment_notifier.settings, "GEMINI_API_KEYS", ""
    ), patch(
        "app.integrations.telegram_client.telegram_client.send_message",
        new=send_mock,
    ):
        ok = await shipment_notifier.notify_delay(
            telegram_user_id=55555,
            customer_name="Mehmet",
            order_id=123,
            days_overdue=4,
            current_location="Bursa Şubesi",
            item_summary="3 Zeytinyağı",
        )
    assert ok is True
    body = send_mock.call_args.args[1]
    assert "Mehmet" in body
    assert "#123" in body
    assert "4 gün" in body
    assert "özür" in body.lower()
