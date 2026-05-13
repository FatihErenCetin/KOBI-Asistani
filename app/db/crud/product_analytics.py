from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product, StockMovement, StockMovementReason


async def for_product(db: AsyncSession, product: Product) -> dict:
    """Tek urun icin KPI seti."""
    now = datetime.utcnow()
    win_30d = now - timedelta(days=30)
    win_7d = now - timedelta(days=7)

    sold_30d = await db.execute(
        select(func.coalesce(func.sum(-StockMovement.delta), 0.0)).where(
            StockMovement.product_id == product.id,
            StockMovement.reason == StockMovementReason.SALE,
            StockMovement.created_at >= win_30d,
        )
    )
    units_30d = float(sold_30d.scalar_one())
    revenue_30d = units_30d * product.price

    sold_7d = await db.execute(
        select(func.coalesce(func.sum(-StockMovement.delta), 0.0)).where(
            StockMovement.product_id == product.id,
            StockMovement.reason == StockMovementReason.SALE,
            StockMovement.created_at >= win_7d,
        )
    )
    units_7d = float(sold_7d.scalar_one())

    velocity = units_30d / 30.0 if units_30d else 0.0
    days_of_stock = (product.stock / velocity) if velocity > 0 else None
    margin_pct = None
    if product.cost > 0 and product.price > 0:
        margin_pct = round((product.price - product.cost) / product.price * 100, 1)

    last_sale = await db.execute(
        select(func.max(StockMovement.created_at)).where(
            StockMovement.product_id == product.id,
            StockMovement.reason == StockMovementReason.SALE,
        )
    )
    last_sale_at = last_sale.scalar_one()

    return {
        "units_sold_30d": units_30d,
        "revenue_30d": round(revenue_30d, 2),
        "units_sold_7d": units_7d,
        "daily_velocity": round(velocity, 2),
        "days_of_stock": round(days_of_stock, 1) if days_of_stock is not None else None,
        "profit_margin_pct": margin_pct,
        "last_sale_at": last_sale_at.isoformat() if last_sale_at else None,
    }


async def daily_sales_sparkline(
    db: AsyncSession, product_id: int, days: int = 7
) -> list[dict]:
    """Son N gunun her biri icin satilan miktar (sparkline icin)."""
    since = datetime.utcnow() - timedelta(days=days)
    res = await db.execute(
        select(
            func.date(StockMovement.created_at).label("day"),
            func.coalesce(func.sum(-StockMovement.delta), 0.0).label("units"),
        )
        .where(
            StockMovement.product_id == product_id,
            StockMovement.reason == StockMovementReason.SALE,
            StockMovement.created_at >= since,
        )
        .group_by("day")
        .order_by("day")
    )
    rows = {str(r.day): float(r.units) for r in res.all()}
    out = []
    for i in range(days):
        d = (datetime.utcnow().date() - timedelta(days=days - 1 - i)).isoformat()
        out.append({"day": d, "units": rows.get(d, 0.0)})
    return out
