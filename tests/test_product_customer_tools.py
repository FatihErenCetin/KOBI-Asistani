import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Product
from app.tools import customer_tools, product_tools
from app.tools.base import AgentContext


@pytest.mark.asyncio
async def test_check_product_availability_finds_alias(db):
    db.add(Product(name="Domates", aliases="salkim domates", unit="kg", price=18, stock=50))
    await db.flush()
    ctx = AgentContext(db=db, customer_id=1)
    result = await product_tools.check_product_availability("salkim", 5.0, ctx=ctx)
    assert result["available"] is True
    assert result["product"]["name"] == "Domates"


@pytest.mark.asyncio
async def test_check_product_availability_low_stock(db):
    db.add(Product(name="Bal", unit="kg", price=200, stock=2))
    await db.flush()
    ctx = AgentContext(db=db, customer_id=1)
    result = await product_tools.check_product_availability("bal", 5.0, ctx=ctx)
    assert result["available"] is False


@pytest.mark.asyncio
async def test_stock_overview_requires_admin(db):
    ctx = AgentContext(db=db, customer_id=1)
    result = await product_tools.stock_overview(ctx=ctx)
    assert "error" in result


@pytest.mark.asyncio
async def test_customer_order_history_by_name(db):
    c = await customers_crud.create(db, name="Ayse Yilmaz")
    p = Product(name="Bal", unit="kg", price=200, stock=10)
    db.add(p)
    await db.flush()
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1.0)])

    ctx = AgentContext(db=db, is_admin=True)
    result = await customer_tools.customer_order_history("Ayse", ctx=ctx)
    assert result["order_count"] == 1
    assert result["total_spend"] == 200.0
