import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import product_analytics as analytics
from app.db.crud import products as products_crud
from app.db.models import StockMovementReason


@pytest.mark.asyncio
async def test_analytics_computes_velocity_and_margin(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 30, reason=StockMovementReason.INITIAL)
    c = await customers_crud.create(db, name="X")
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 3.0)])
    await db.commit()

    data = await analytics.for_product(db, p)
    assert data["profit_margin_pct"] == 40.0
    assert data["units_sold_7d"] >= 3.0
    assert data["daily_velocity"] >= 0.1


@pytest.mark.asyncio
async def test_analytics_zero_when_no_sales(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    data = await analytics.for_product(db, p)
    assert data["units_sold_30d"] == 0
    assert data["units_sold_7d"] == 0
    assert data["daily_velocity"] == 0
    assert data["days_of_stock"] is None
    assert data["last_sale_at"] is None


@pytest.mark.asyncio
async def test_sparkline_returns_n_days(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    series = await analytics.daily_sales_sparkline(db, p.id, days=7)
    assert len(series) == 7
    assert all("day" in r and "units" in r for r in series)


@pytest.mark.asyncio
async def test_sparkline_aggregates_per_day(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 20, reason=StockMovementReason.INITIAL)
    c = await customers_crud.create(db, name="X")
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 2.0)])
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.5)])
    await db.commit()

    series = await analytics.daily_sales_sparkline(db, p.id, days=7)
    # Today's bucket should have 3.5
    today_bucket = series[-1]
    assert today_bucket["units"] == 3.5
