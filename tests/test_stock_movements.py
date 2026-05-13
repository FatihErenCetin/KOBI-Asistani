import pytest

from app.db.crud import products as products_crud
from app.db.crud import stock_movements as sm_crud
from app.db.models import StockMovementReason


@pytest.mark.asyncio
async def test_adjust_stock_writes_movement_and_updates_balance(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(
        db, p, 10.0, reason=StockMovementReason.PURCHASE, note="Ilk alim"
    )
    assert p.stock == 10.0
    movements = await sm_crud.list_for_product(db, p.id)
    purchase = [m for m in movements if m.reason == StockMovementReason.PURCHASE]
    assert len(purchase) == 1
    assert purchase[0].delta == 10.0
    assert purchase[0].balance_after == 10.0


@pytest.mark.asyncio
async def test_set_stock_records_adjustment_delta(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 10, reason=StockMovementReason.PURCHASE)
    await products_crud.set_stock(db, p, 7, note="Sayim duzeltme")
    assert p.stock == 7
    movements = await sm_crud.list_for_product(db, p.id)
    adjustment = [m for m in movements if m.reason == StockMovementReason.ADJUSTMENT]
    assert len(adjustment) == 1
    assert adjustment[0].delta == -3.0


@pytest.mark.asyncio
async def test_set_stock_noop_when_unchanged(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 5, reason=StockMovementReason.PURCHASE)
    before = len(await sm_crud.list_for_product(db, p.id))
    await products_crud.set_stock(db, p, 5)
    assert len(await sm_crud.list_for_product(db, p.id)) == before


@pytest.mark.asyncio
async def test_negative_balance_clamped(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 5, reason=StockMovementReason.PURCHASE)
    # Try to remove more than available
    await products_crud.adjust_stock(db, p, -10, reason=StockMovementReason.SALE)
    assert p.stock == 0.0
