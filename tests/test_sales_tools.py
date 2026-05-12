import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Product
from app.tools import order_tools
from app.tools.base import AgentContext


@pytest.mark.asyncio
async def test_sales_summary_by_day(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])

    ctx = AgentContext(db=db, is_admin=True)
    result = await order_tools.sales_summary(since_days=1, group_by="day", ctx=ctx)
    assert result["total_revenue"] == 200.0
    assert len(result["rows"]) >= 1


@pytest.mark.asyncio
async def test_top_products(db):
    c = await customers_crud.create(db, name="Test")
    bal = Product(name="Bal", unit="kg", price=200, stock=10)
    zeytin = Product(name="Zeytin", unit="lt", price=300, stock=10)
    db.add(bal)
    db.add(zeytin)
    await db.flush()
    await orders_crud.create_order(db, customer_id=c.id, items=[(bal, 2.0), (zeytin, 1.0)])

    ctx = AgentContext(db=db, is_admin=True)
    result = await order_tools.top_products(ctx=ctx)
    assert result["top"][0]["product"] in ("Bal", "Zeytin")
