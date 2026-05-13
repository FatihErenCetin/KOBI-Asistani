"""M7: Lot/batch + FIFO."""

from datetime import date, datetime, timedelta

import pytest

from app.db.crud import products as products_crud
from app.db.crud import stock_balances as sb_crud
from app.db.crud import stock_lots as lots_crud
from app.db.crud.stock_lots import InsufficientStock


@pytest.mark.asyncio
async def test_create_lot(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="L001",
        quantity=10,
        expiry_date=date.today() + timedelta(days=30),
    )
    assert lot.id is not None
    assert lot.quantity == 10


@pytest.mark.asyncio
async def test_fifo_consumes_closest_expiry_first(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    # Daha geç expiry — önce yazılan
    far_lot = await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="FAR",
        quantity=5, expiry_date=date.today() + timedelta(days=30),
        received_at=datetime.utcnow() - timedelta(days=10),
    )
    # Daha yakın expiry — sonra yazılan
    near_lot = await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="NEAR",
        quantity=5, expiry_date=date.today() + timedelta(days=5),
        received_at=datetime.utcnow(),
    )
    consumed = await lots_crud.consume_fifo(
        db, product_id=p.id, warehouse_id=default.id, qty=3
    )
    # Yakın expiry önce tüketilmeli
    assert consumed[0][0].id == near_lot.id
    assert consumed[0][1] == 3
    # Far lot dokunmadı
    assert far_lot.quantity == 5


@pytest.mark.asyncio
async def test_fifo_spans_multiple_lots(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    a = await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="A",
        quantity=3, expiry_date=date.today() + timedelta(days=5),
    )
    b = await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="B",
        quantity=5, expiry_date=date.today() + timedelta(days=15),
    )
    # Toplam 8, 6 tüket → a tamamen, b'den 3
    consumed = await lots_crud.consume_fifo(
        db, product_id=p.id, warehouse_id=default.id, qty=6
    )
    assert len(consumed) == 2
    assert a.quantity == 0
    assert b.quantity == 2


@pytest.mark.asyncio
async def test_fifo_insufficient_raises(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="A", quantity=2,
    )
    with pytest.raises(InsufficientStock):
        await lots_crud.consume_fifo(
            db, product_id=p.id, warehouse_id=default.id, qty=10
        )


@pytest.mark.asyncio
async def test_fifo_empty_returns_empty_list(db):
    """Lot olmayan urunde FIFO bos liste doner (fallback davranis)."""
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    consumed = await lots_crud.consume_fifo(
        db, product_id=p.id, warehouse_id=default.id, qty=5
    )
    assert consumed == []


@pytest.mark.asyncio
async def test_expiring_soon(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    near = await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="NEAR",
        quantity=3, expiry_date=date.today() + timedelta(days=5),
    )
    await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="FAR",
        quantity=3, expiry_date=date.today() + timedelta(days=60),
    )
    await lots_crud.create(
        db, product_id=p.id, warehouse_id=default.id, lot_number="NO_EXPIRY",
        quantity=3, expiry_date=None,
    )
    rows = await lots_crud.expiring_soon(db, within_days=14)
    assert len(rows) == 1
    assert rows[0].id == near.id
