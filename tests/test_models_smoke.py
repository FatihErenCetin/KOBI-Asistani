import pytest

from app.db.models import Customer, Order, OrderStatus, Product


@pytest.mark.asyncio
async def test_create_customer(db):
    c = Customer(name="Test", phone="+905551112233")
    db.add(c)
    await db.commit()
    assert c.id is not None


@pytest.mark.asyncio
async def test_create_order_with_items(db):
    c = Customer(name="Test", phone="+905551112233")
    db.add(c)
    await db.flush()

    p = Product(name="Bal", unit="kg", price=200.0, stock=10)
    db.add(p)
    await db.flush()

    o = Order(customer_id=c.id, status=OrderStatus.PENDING, total=200.0)
    db.add(o)
    await db.commit()
    assert o.id is not None
