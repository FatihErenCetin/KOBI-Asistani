from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceHistory, PriceHistoryField


async def record(
    db: AsyncSession,
    *,
    product_id: int,
    field: PriceHistoryField,
    old_value: float | None,
    new_value: float,
    reason: str | None = None,
    admin_id: int | None = None,
) -> PriceHistory:
    row = PriceHistory(
        product_id=product_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        changed_by_admin_id=admin_id,
    )
    db.add(row)
    await db.flush()
    return row


async def list_for_product(
    db: AsyncSession, product_id: int, limit: int = 50
) -> list[PriceHistory]:
    res = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(desc(PriceHistory.changed_at))
        .limit(limit)
    )
    return list(res.scalars())
