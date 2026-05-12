import pytest

from app.db.crud import customers as customers_crud
from app.db.models import Product
from app.tools import order_tools
from app.tools.base import AgentContext


@pytest.mark.asyncio
async def test_draft_then_confirm_flow(db):
    c = await customers_crud.create(db, name="Test", telegram_user_id=12345)
    db.add(Product(name="Bal", unit="kg", price=200, stock=10))
    await db.flush()

    ctx = AgentContext(db=db, customer_id=c.id, telegram_user_id=12345)
    draft = await order_tools.create_order_draft(
        [{"product_name": "bal", "quantity": 2.0}], ctx=ctx
    )
    assert "draft_id" in draft
    assert draft["total"] == 400.0

    confirmed = await order_tools.confirm_order(draft["draft_id"], ctx=ctx)
    assert "order_id" in confirmed
    assert confirmed["total"] == 400.0


@pytest.mark.asyncio
async def test_draft_insufficient_stock(db):
    c = await customers_crud.create(db, name="Test", telegram_user_id=12345)
    db.add(Product(name="Bal", unit="kg", price=200, stock=1))
    await db.flush()

    ctx = AgentContext(db=db, customer_id=c.id, telegram_user_id=12345)
    result = await order_tools.create_order_draft(
        [{"product_name": "bal", "quantity": 5.0}], ctx=ctx
    )
    assert "error" in result
