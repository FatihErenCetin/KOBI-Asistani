from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, StockMovement, StockMovementReason


async def record(
    db: AsyncSession,
    *,
    product: Product,
    delta: float,
    reason: StockMovementReason,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
    admin_id: int | None = None,
) -> StockMovement:
    """Stok hareketini yazar VE Product.stock'u guncellr. Tek atomik nokta."""
    new_balance = max(0.0, product.stock + delta)
    product.stock = new_balance
    row = StockMovement(
        product_id=product.id,
        delta=delta,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        balance_after=new_balance,
        created_by_admin_id=admin_id,
    )
    db.add(row)
    await db.flush()
    return row


async def list_for_product(
    db: AsyncSession, product_id: int, limit: int = 100
) -> list[StockMovement]:
    res = await db.execute(
        select(StockMovement)
        .where(StockMovement.product_id == product_id)
        .order_by(desc(StockMovement.created_at))
        .limit(limit)
    )
    return list(res.scalars())
