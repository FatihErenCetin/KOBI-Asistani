"""Proaktif risk scanner — bulgudan complaint kaydina end-to-end akis."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.db.crud import complaints as complaints_crud
from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import (
    CustomerComplaint,
    OrderStatus,
    Product,
    Shipment,
    ShipmentStatus,
)
from app.services import proactive_risk_scanner


@pytest.mark.asyncio
async def test_scan_creates_complaint_for_delayed_shipment(db):
    """Gecikmiş kargo → yeni complaint (auto_generated=True, source=shipment_delay)."""
    c = await customers_crud.create(db, name="Geciken Ali")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    o.status = OrderStatus.SHIPPED
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-LATE",
        carrier="MockKargo",
        status=ShipmentStatus.IN_TRANSIT,
        estimated_delivery=date.today() - timedelta(days=4),
        last_event_at=datetime.utcnow() - timedelta(days=6),
    )
    db.add(s)
    await db.flush()

    # LLM mock'la (gerçek Gemini çağrısı yapmasın)
    with patch.object(
        proactive_risk_scanner,
        "_llm_narrate",
        new=AsyncMock(
            return_value=("Kargo geç kaldı: #" + str(o.id), "4 gün gecikme tespit edildi.")
        ),
    ):
        summary = await proactive_risk_scanner.scan_and_report(db)

    assert summary["shipment_delay"] >= 1

    rows = await complaints_crud.list_open(db)
    target = next(
        (r for r in rows if r.source == "shipment_delay" and r.related_entity_id == s.id),
        None,
    )
    assert target is not None
    assert target.auto_generated is True
    assert target.customer_id == c.id
    assert "geç kaldı" in target.subject.lower() or "#" in target.subject
    assert target.description is not None


@pytest.mark.asyncio
async def test_scan_dedupes_within_24h(db):
    """Aynı entity için 24 saat içinde 2. kayıt atılır."""
    c = await customers_crud.create(db, name="Tekrar")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    o.status = OrderStatus.SHIPPED
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-DUP",
        carrier="MockKargo",
        status=ShipmentStatus.IN_TRANSIT,
        estimated_delivery=date.today() - timedelta(days=2),
        last_event_at=datetime.utcnow() - timedelta(days=4),
    )
    db.add(s)
    await db.flush()

    with patch.object(
        proactive_risk_scanner,
        "_llm_narrate",
        new=AsyncMock(return_value=("Test konu", "Test açıklama")),
    ):
        first = await proactive_risk_scanner.scan_and_report(db)
        second = await proactive_risk_scanner.scan_and_report(db)

    assert first["shipment_delay"] >= 1
    assert second["shipment_delay"] == 0  # mükerrer engellendi


@pytest.mark.asyncio
async def test_scan_creates_for_stale_pending(db):
    c = await customers_crud.create(db, name="Bekleyen")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 2)])
    o.created_at = datetime.utcnow() - timedelta(hours=48)
    await db.flush()

    with patch.object(
        proactive_risk_scanner,
        "_llm_narrate",
        new=AsyncMock(return_value=("Bekleyen sipariş", "48 saat bekledi.")),
    ):
        summary = await proactive_risk_scanner.scan_and_report(db)

    assert summary["stale_pending"] >= 1
    rows = await complaints_crud.list_open(db)
    assert any(
        r.source == "stale_pending" and r.related_entity_id == o.id for r in rows
    )


@pytest.mark.asyncio
async def test_resolved_complaint_does_not_block_new_one(db):
    """Mükerrer engelleme sadece OPEN kayıtlar için — resolved kaydı engellemez."""
    c = await customers_crud.create(db, name="X")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    o.status = OrderStatus.SHIPPED
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-OK",
        carrier="MockKargo",
        status=ShipmentStatus.IN_TRANSIT,
        estimated_delivery=date.today() - timedelta(days=1),
        last_event_at=datetime.utcnow() - timedelta(days=3),
    )
    db.add(s)
    await db.flush()

    with patch.object(
        proactive_risk_scanner,
        "_llm_narrate",
        new=AsyncMock(return_value=("X", "Y")),
    ):
        first = await proactive_risk_scanner.scan_and_report(db)
        # İlk complaint'ı resolved işaretle
        rows = await complaints_crud.list_open(db)
        delayed = next(r for r in rows if r.source == "shipment_delay")
        await complaints_crud.mark_resolved(db, delayed)
        await db.commit()
        # Tekrar tara → yeni kayıt oluşmalı (önceki resolved olduğu için)
        second = await proactive_risk_scanner.scan_and_report(db)

    assert first["shipment_delay"] >= 1
    assert second["shipment_delay"] >= 1
