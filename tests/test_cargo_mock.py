import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Product, ShipmentStatus
from app.integrations import cargo_mock


@pytest.mark.asyncio
async def test_create_shipment_and_advance(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    order = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])

    shipment = await cargo_mock.create_shipment(db, order)
    assert shipment.tracking_no.startswith("TR")
    assert shipment.status == ShipmentStatus.LABEL_CREATED

    await cargo_mock.advance(db, shipment)
    assert shipment.status == ShipmentStatus.PICKED_UP

    for _ in range(5):
        await cargo_mock.advance(db, shipment)
    assert shipment.status == ShipmentStatus.DELIVERED


@pytest.mark.asyncio
async def test_advance_at_terminal_state_is_noop(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    order = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])
    shipment = await cargo_mock.create_shipment(db, order)

    for _ in range(10):
        await cargo_mock.advance(db, shipment)
    assert shipment.status == ShipmentStatus.DELIVERED
