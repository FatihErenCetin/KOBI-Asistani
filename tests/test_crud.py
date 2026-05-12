from datetime import datetime, timedelta

import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.models import Product


@pytest.mark.asyncio
async def test_customer_create_and_link_telegram(db):
    c = await customers_crud.create(db, name="Ayse", phone="+905551112233")
    await customers_crud.link_telegram(db, c, telegram_user_id=12345)
    fetched = await customers_crud.get_by_telegram(db, 12345)
    assert fetched is not None
    assert fetched.name == "Ayse"


@pytest.mark.asyncio
async def test_product_search_by_alias(db):
    p = Product(
        name="Domates", aliases="salkim domates,kuru domates", unit="kg", price=18, stock=50
    )
    db.add(p)
    await db.flush()
    results = await products_crud.search_by_name(db, "salkim")
    assert len(results) == 1
    assert results[0].name == "Domates"


@pytest.mark.asyncio
async def test_create_order_reduces_stock(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    order = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 3.0)])
    assert order.total == 600.0
    assert p.stock == 7.0


@pytest.mark.asyncio
async def test_revenue_since(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])
    rev = await orders_crud.revenue_since(db, datetime.utcnow() - timedelta(hours=1))
    assert rev == 200.0
