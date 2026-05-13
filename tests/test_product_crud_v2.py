import pytest

from app.db.crud import price_history as ph_crud
from app.db.crud import products as products_crud
from app.db.models import PriceHistoryField


@pytest.mark.asyncio
async def test_create_writes_initial_price_and_cost_history(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    history = await ph_crud.list_for_product(db, p.id)
    fields = {h.field for h in history}
    assert PriceHistoryField.PRICE in fields
    assert PriceHistoryField.COST in fields


@pytest.mark.asyncio
async def test_create_without_cost_does_not_write_cost_history(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=0)
    history = await ph_crud.list_for_product(db, p.id)
    fields = {h.field for h in history}
    assert PriceHistoryField.PRICE in fields
    assert PriceHistoryField.COST not in fields


@pytest.mark.asyncio
async def test_update_price_creates_history_row(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    initial = len(await ph_crud.list_for_product(db, p.id))
    await products_crud.update(db, p, price=220, reason="Sezonluk artis")
    history = await ph_crud.list_for_product(db, p.id)
    assert len(history) == initial + 1
    latest = history[0]
    assert latest.field == PriceHistoryField.PRICE
    assert latest.old_value == 200
    assert latest.new_value == 220
    assert latest.reason == "Sezonluk artis"


@pytest.mark.asyncio
async def test_update_same_price_does_not_create_history(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    initial = len(await ph_crud.list_for_product(db, p.id))
    await products_crud.update(db, p, price=200)
    assert len(await ph_crud.list_for_product(db, p.id)) == initial


@pytest.mark.asyncio
async def test_soft_delete_hides_from_default_list(db):
    p = await products_crud.create(db, name="Gecici", unit="kg", price=10, cost=5)
    await products_crud.soft_delete(db, p)
    rows = await products_crud.list_all(db)
    assert all(r.id != p.id for r in rows)
    rows_all = await products_crud.list_all(db, include_inactive=True)
    assert any(r.id == p.id for r in rows_all)
