"""Proaktif risk detector'larin unit testleri."""

from datetime import date, datetime, timedelta

import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import (
    CustomerComplaint,
    Order,
    OrderStatus,
    Product,
    Shipment,
    ShipmentStatus,
)
from app.services import risk_detectors


@pytest.mark.asyncio
async def test_find_delayed_shipments(db):
    c = await customers_crud.create(db, name="Ali")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    o.status = OrderStatus.SHIPPED
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-DELAY",
        carrier="MockKargo",
        status=ShipmentStatus.IN_TRANSIT,
        estimated_delivery=date.today() - timedelta(days=3),
        last_event_at=datetime.utcnow() - timedelta(days=5),
    )
    db.add(s)
    await db.flush()

    rows = await risk_detectors.find_delayed_shipments(db)
    assert any(r["tracking_no"] == "TR-DELAY" and r["days_overdue"] == 3 for r in rows)


@pytest.mark.asyncio
async def test_delivered_shipment_not_in_delayed(db):
    c = await customers_crud.create(db, name="Ali")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    s = Shipment(
        order_id=o.id,
        tracking_no="TR-DONE",
        carrier="MockKargo",
        status=ShipmentStatus.DELIVERED,
        estimated_delivery=date.today() - timedelta(days=10),
        last_event_at=datetime.utcnow(),
    )
    db.add(s)
    await db.flush()
    rows = await risk_detectors.find_delayed_shipments(db)
    assert all(r["tracking_no"] != "TR-DONE" for r in rows)


@pytest.mark.asyncio
async def test_find_stale_pending_orders(db):
    c = await customers_crud.create(db, name="Eski Sipariş")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    # 36 saat öncesine al
    o.created_at = datetime.utcnow() - timedelta(hours=36)
    await db.flush()
    rows = await risk_detectors.find_stale_pending_orders(db, hours_threshold=24)
    assert any(r["order_id"] == o.id and r["hours_pending"] >= 24 for r in rows)


@pytest.mark.asyncio
async def test_fresh_pending_not_in_stale(db):
    c = await customers_crud.create(db, name="Yeni")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    # 1 saat önce → stale değil
    o.created_at = datetime.utcnow() - timedelta(hours=1)
    await db.flush()
    rows = await risk_detectors.find_stale_pending_orders(db, hours_threshold=24)
    assert all(r["order_id"] != o.id for r in rows)


@pytest.mark.asyncio
async def test_find_repeat_complainers(db):
    c = await customers_crud.create(db, name="Sürekli Şikayetçi")
    for i in range(3):
        db.add(
            CustomerComplaint(
                customer_id=c.id,
                subject=f"Şikayet {i}",
                risk_score=0.8,
                source="telegram_message",
                message_text="iade",
            )
        )
    await db.flush()
    rows = await risk_detectors.find_repeat_complainers(db, min_count=2)
    target = next((r for r in rows if r["customer_id"] == c.id), None)
    assert target is not None
    assert target["complaint_count"] == 3


@pytest.mark.asyncio
async def test_find_dormant_customers(db):
    c = await customers_crud.create(db, name="Dormant")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    # 5 eski sipariş, hepsi 90 gün önce
    for _ in range(5):
        o = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
        o.created_at = datetime.utcnow() - timedelta(days=90)
    await db.flush()

    rows = await risk_detectors.find_dormant_customers(db, days_silent=60, min_prior_orders=3)
    target = next((r for r in rows if r["customer_id"] == c.id), None)
    assert target is not None
    assert target["prior_order_count"] == 5
    assert target["days_silent"] >= 60


@pytest.mark.asyncio
async def test_active_customer_not_dormant(db):
    c = await customers_crud.create(db, name="Active")
    p = Product(name="X", unit="kg", price=10, cost=5)
    db.add(p)
    await db.flush()
    for _ in range(5):
        await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])
    await db.flush()
    rows = await risk_detectors.find_dormant_customers(db, days_silent=60)
    assert all(r["customer_id"] != c.id for r in rows)
