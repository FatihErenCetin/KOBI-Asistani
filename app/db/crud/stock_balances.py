"""Per-warehouse stock balance operations.

Product.stock kolonu denormalize cache olarak korunur — toplam = SUM(balance.quantity).
Tek yazma kanali: stock_movements_crud.record. Tutarlilik orada saglanir.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import StockBalance, Warehouse


async def get_or_create(
    db: AsyncSession, product_id: int, warehouse_id: int
) -> StockBalance:
    res = await db.execute(
        select(StockBalance).where(
            StockBalance.product_id == product_id,
            StockBalance.warehouse_id == warehouse_id,
        )
    )
    b = res.scalar_one_or_none()
    if b is None:
        b = StockBalance(
            product_id=product_id, warehouse_id=warehouse_id, quantity=0
        )
        db.add(b)
        await db.flush()
    return b


async def adjust(
    db: AsyncSession, product_id: int, warehouse_id: int, delta: float
) -> float:
    """Bakiyeyi delta kadar degistirir, yeni miktari doner. Negatife clamp."""
    b = await get_or_create(db, product_id, warehouse_id)
    b.quantity = max(0.0, b.quantity + delta)
    await db.flush()
    return b.quantity


async def total_for_product(db: AsyncSession, product_id: int) -> float:
    res = await db.execute(
        select(func.coalesce(func.sum(StockBalance.quantity), 0.0)).where(
            StockBalance.product_id == product_id
        )
    )
    return float(res.scalar_one())


async def breakdown_for_product(
    db: AsyncSession, product_id: int
) -> list[StockBalance]:
    res = await db.execute(
        select(StockBalance)
        .where(StockBalance.product_id == product_id)
        .options(selectinload(StockBalance.warehouse))
        .order_by(StockBalance.warehouse_id)
    )
    return list(res.scalars())


async def get_default_warehouse(db: AsyncSession) -> Warehouse | None:
    """Ana depoyu doner (is_default=TRUE)."""
    res = await db.execute(
        select(Warehouse).where(Warehouse.is_default.is_(True)).limit(1)
    )
    return res.scalar_one_or_none()
