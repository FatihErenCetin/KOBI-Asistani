from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductSupplier,
    StockMovement,
    StockMovementReason,
    Supplier,
)


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

    # Revenue: OrderItem.unit_price ile join — gecmis fiyat degisikliklerini saygi tut
    revenue_q = await db.execute(
        select(
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0.0)
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            OrderItem.product_id == product.id,
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= win_30d,
        )
    )
    revenue_30d = float(revenue_q.scalar_one())

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


async def bulk_sparklines(
    db: AsyncSession, product_ids: list[int], days: int = 7
) -> dict[int, list[dict]]:
    """Toplu sparkline. {product_id: [{day, units}, ...]} doner. Tek sorgu."""
    if not product_ids:
        return {}
    since = datetime.utcnow() - timedelta(days=days)
    res = await db.execute(
        select(
            StockMovement.product_id,
            func.date(StockMovement.created_at).label("day"),
            func.coalesce(func.sum(-StockMovement.delta), 0.0).label("units"),
        )
        .where(
            StockMovement.product_id.in_(product_ids),
            StockMovement.reason == StockMovementReason.SALE,
            StockMovement.created_at >= since,
        )
        .group_by(StockMovement.product_id, "day")
    )
    by_pid: dict[int, dict[str, float]] = {pid: {} for pid in product_ids}
    for r in res.all():
        by_pid[r.product_id][str(r.day)] = float(r.units)
    out: dict[int, list[dict]] = {}
    today = datetime.utcnow().date()
    for pid in product_ids:
        series = []
        for i in range(days):
            d = (today - timedelta(days=days - 1 - i)).isoformat()
            series.append({"day": d, "units": by_pid[pid].get(d, 0.0)})
        out[pid] = series
    return out


async def low_margin_products(
    db: AsyncSession, margin_threshold: float = 20, limit: int = 30
) -> list[dict]:
    """Marji esik altinda olan aktif urunler (kar marji = (price - cost) / price * 100)."""
    res = await db.execute(
        select(Product)
        .where(Product.is_active.is_(True), Product.cost > 0, Product.price > 0)
        .order_by(Product.name)
    )
    rows = []
    for p in res.scalars():
        margin = round((p.price - p.cost) / p.price * 100, 1)
        if margin < margin_threshold:
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "unit": p.unit,
                    "price": p.price,
                    "cost": p.cost,
                    "margin_pct": margin,
                    "stock": p.stock,
                }
            )
    return sorted(rows, key=lambda r: r["margin_pct"])[:limit]


async def fast_depleting_products(
    db: AsyncSession, max_days: float = 7, limit: int = 30
) -> list[dict]:
    """Mevcut satis hiziyla N gun icinde bitecek aktif urunler."""
    res = await db.execute(
        select(Product).where(Product.is_active.is_(True), Product.stock > 0)
    )
    rows = []
    for p in res.scalars():
        analytics = await for_product(db, p)
        dos = analytics["days_of_stock"]
        if dos is not None and dos <= max_days:
            rows.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "unit": p.unit,
                    "stock": p.stock,
                    "daily_velocity": analytics["daily_velocity"],
                    "days_of_stock": dos,
                }
            )
    return sorted(rows, key=lambda r: r["days_of_stock"])[:limit]


async def supplier_lead_time_stats(db: AsyncSession) -> list[dict]:
    """Her tedarikci icin ortalama lead_time + bagli urun sayisi + son alis tarihi."""
    res = await db.execute(
        select(
            Supplier.id,
            Supplier.name,
            func.avg(ProductSupplier.lead_time_days).label("avg_lead"),
            func.count(ProductSupplier.id).label("n_products"),
            func.max(ProductSupplier.last_purchase_at).label("last_purchase"),
        )
        .outerjoin(ProductSupplier, ProductSupplier.supplier_id == Supplier.id)
        .where(Supplier.is_active.is_(True))
        .group_by(Supplier.id, Supplier.name)
        .order_by(Supplier.name)
    )
    return [
        {
            "supplier_id": r.id,
            "supplier_name": r.name,
            "avg_lead_time_days": round(float(r.avg_lead), 1) if r.avg_lead else None,
            "linked_product_count": int(r.n_products or 0),
            "last_purchase_at": r.last_purchase.isoformat() if r.last_purchase else None,
        }
        for r in res.all()
    ]


async def category_stock_overview(db: AsyncSession) -> list[dict]:
    """Kategori bazinda urun sayisi + toplam stok + dusuk stok sayisi."""
    low_case = case(
        (Product.stock <= Product.low_stock_threshold, 1), else_=0
    )
    res = await db.execute(
        select(
            Product.category,
            func.count(Product.id).label("n"),
            func.coalesce(func.sum(Product.stock), 0.0).label("total_stock"),
            func.coalesce(func.sum(low_case), 0).label("n_low"),
        )
        .where(Product.is_active.is_(True))
        .group_by(Product.category)
        .order_by(Product.category)
    )
    return [
        {
            "category": r.category or "Kategorisiz",
            "product_count": int(r.n),
            "total_stock": float(r.total_stock or 0),
            "low_stock_count": int(r.n_low or 0),
        }
        for r in res.all()
    ]
