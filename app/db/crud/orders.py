from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.crud import stock_movements as stock_movements_crud
from app.db.models import Order, OrderItem, OrderStatus, Product, StockMovementReason


async def get_by_id(db: AsyncSession, order_id: int) -> Order | None:
    res = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.shipment),
            selectinload(Order.customer),
        )
    )
    return res.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    *,
    status: OrderStatus | None = None,
    since: datetime | None = None,
    customer_id: int | None = None,
    limit: int = 20,
) -> list[Order]:
    stmt = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product),
        selectinload(Order.shipment),
        selectinload(Order.customer),
    )
    if status:
        stmt = stmt.where(Order.status == status)
    if since:
        stmt = stmt.where(Order.created_at >= since)
    if customer_id:
        stmt = stmt.where(Order.customer_id == customer_id)
    stmt = stmt.order_by(Order.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars())


async def create_order(
    db: AsyncSession,
    *,
    customer_id: int,
    items: list[tuple[Product, float]],
    note: str | None = None,
    warehouse_id: int | None = None,
) -> Order:
    """warehouse_id verilmezse default depo kullanılır."""
    total = sum(p.price * qty for p, qty in items)
    order = Order(customer_id=customer_id, status=OrderStatus.PENDING, total=total, note=note)
    db.add(order)
    await db.flush()
    for product, qty in items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                unit_price=product.price,
            )
        )
        await stock_movements_crud.record(
            db,
            product=product,
            delta=-qty,
            reason=StockMovementReason.SALE,
            warehouse_id=warehouse_id,
            reference_type="order",
            reference_id=order.id,
        )
    await db.flush()
    return order


async def update_status(db: AsyncSession, order: Order, new_status: OrderStatus) -> Order:
    order.status = new_status
    await db.flush()
    return order


async def revenue_since(db: AsyncSession, since: datetime) -> float:
    res = await db.execute(
        select(func.coalesce(func.sum(Order.total), 0.0))
        .where(Order.created_at >= since)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    return float(res.scalar_one())


async def count_by_status(db: AsyncSession, status: OrderStatus) -> int:
    res = await db.execute(select(func.count(Order.id)).where(Order.status == status))
    return int(res.scalar_one())
