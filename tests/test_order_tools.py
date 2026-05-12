import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Product
from app.tools import order_tools
from app.tools.base import AgentContext


@pytest.mark.asyncio
async def test_get_my_order_status_owner_can_see(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    order = await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])

    ctx = AgentContext(db=db, customer_id=c.id)
    result = await order_tools.get_my_order_status(order.id, ctx=ctx)
    assert result["order_id"] == order.id
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_my_order_status_blocks_other_customer(db):
    c1 = await customers_crud.create(db, name="A")
    c2 = await customers_crud.create(db, name="B")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    order = await orders_crud.create_order(db, customer_id=c1.id, items=[(p, 1.0)])

    ctx = AgentContext(db=db, customer_id=c2.id)
    result = await order_tools.get_my_order_status(order.id, ctx=ctx)
    assert "error" in result


@pytest.mark.asyncio
async def test_list_orders_requires_admin(db):
    ctx = AgentContext(db=db, customer_id=1)
    result = await order_tools.list_orders(ctx=ctx)
    assert "error" in result


@pytest.mark.asyncio
async def test_list_orders_admin_works(db):
    c = await customers_crud.create(db, name="Test")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])

    ctx = AgentContext(db=db, is_admin=True)
    result = await order_tools.list_orders(ctx=ctx)
    assert result["count"] >= 1
