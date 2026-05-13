"""Finansal analiz hesaplayicilari.

Formuller:
- Revenue (Gelir) = SUM(OrderItem.quantity × unit_price) WHERE order.status != CANCELLED
- COGS (Cost of Goods Sold) = SUM(OrderItem.quantity × product.cost) — yaklasik
  (Tam dogru: satis anindaki maliyet PriceHistory'den. Hackathon: current cost.)
- Brut Kar = Revenue − COGS
- OpEx (Operasyonel Gider) = SUM(Expense.amount)
- Net Kar = Brut Kar − OpEx
- Brut Marj %% = Brut Kar / Revenue × 100
- Net Marj %% = Net Kar / Revenue × 100
"""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Expense,
    ExpenseCategory,
    Order,
    OrderItem,
    OrderStatus,
    Product,
)


def _zero_if_none(v):
    return float(v) if v is not None else 0.0


async def _revenue_and_cogs(
    db: AsyncSession, since: datetime, until: datetime | None = None
) -> tuple[float, float]:
    """Belirli tarih araliginda gelir ve COGS toplamlari."""
    until = until or datetime.utcnow()
    # Revenue: OrderItem.qty × unit_price
    rev_q = await db.execute(
        select(
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0.0)
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= since,
            Order.created_at <= until,
        )
    )
    revenue = float(rev_q.scalar_one())

    # COGS: OrderItem.qty × product.cost
    cogs_q = await db.execute(
        select(func.coalesce(func.sum(OrderItem.quantity * Product.cost), 0.0))
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= since,
            Order.created_at <= until,
        )
    )
    cogs = float(cogs_q.scalar_one())
    return revenue, cogs


async def _expenses_total(
    db: AsyncSession, since: datetime, until: datetime | None = None
) -> float:
    until = until or datetime.utcnow()
    res = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.incurred_at >= since, Expense.incurred_at <= until
        )
    )
    return float(res.scalar_one())


async def period_summary(
    db: AsyncSession, *, since_days: int = 30
) -> dict:
    """Belirtilen son N gunun finansal ozeti.

    + Onceki ayni periyot ile kiyas (delta_pct).
    """
    now = datetime.utcnow()
    since = now - timedelta(days=since_days)
    prev_since = since - timedelta(days=since_days)
    prev_until = since

    revenue, cogs = await _revenue_and_cogs(db, since, now)
    opex = await _expenses_total(db, since, now)
    gross_profit = revenue - cogs
    net_profit = gross_profit - opex
    gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0.0
    net_margin = (net_profit / revenue * 100) if revenue > 0 else 0.0

    # Önceki dönem
    prev_revenue, prev_cogs = await _revenue_and_cogs(db, prev_since, prev_until)
    prev_opex = await _expenses_total(db, prev_since, prev_until)
    prev_net = (prev_revenue - prev_cogs) - prev_opex

    def _delta(now_v: float, prev_v: float) -> float | None:
        if prev_v == 0:
            return None
        return round((now_v - prev_v) / abs(prev_v) * 100, 1)

    return {
        "since": since.isoformat(),
        "until": now.isoformat(),
        "since_days": since_days,
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "operating_expenses": round(opex, 2),
        "net_profit": round(net_profit, 2),
        "gross_margin_pct": round(gross_margin, 1),
        "net_margin_pct": round(net_margin, 1),
        "prev_revenue": round(prev_revenue, 2),
        "prev_net_profit": round(prev_net, 2),
        "revenue_change_pct": _delta(revenue, prev_revenue),
        "net_profit_change_pct": _delta(net_profit, prev_net),
    }


async def category_breakdown(
    db: AsyncSession, *, since_days: int = 30
) -> list[dict]:
    """Gider kategorilerinin son N gundeki dagilimi."""
    since = datetime.utcnow() - timedelta(days=since_days)
    res = await db.execute(
        select(
            Expense.category,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("n"),
        )
        .where(Expense.incurred_at >= since)
        .group_by(Expense.category)
    )
    rows = res.all()
    grand_total = sum(float(r.total or 0) for r in rows) or 1.0
    out = []
    for r in rows:
        total = float(r.total or 0)
        out.append(
            {
                "category": r.category.value,
                "total": round(total, 2),
                "share_pct": round(total / grand_total * 100, 1),
                "count": int(r.n),
            }
        )
    return sorted(out, key=lambda x: x["total"], reverse=True)


async def monthly_trend(
    db: AsyncSession, *, months: int = 6
) -> list[dict]:
    """Son N ay icin aylik revenue, cogs, opex, net trendi."""
    now = datetime.utcnow()
    # Aylari hesapla (bugünden geriye doğru)
    buckets: dict[str, dict] = {}
    for i in range(months):
        # Ayin ilk gunu
        target = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        key = target.strftime("%Y-%m")
        buckets[key] = {
            "month": key,
            "revenue": 0.0,
            "cogs": 0.0,
            "opex": 0.0,
            "net": 0.0,
        }

    earliest = min(buckets.keys())
    since = datetime.strptime(earliest + "-01", "%Y-%m-%d")

    # Revenue + COGS query (group by ay)
    res = await db.execute(
        select(
            func.to_char(Order.created_at, "YYYY-MM").label("ym"),
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.unit_price), 0.0
            ).label("rev"),
            func.coalesce(
                func.sum(OrderItem.quantity * Product.cost), 0.0
            ).label("cogs"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= since,
        )
        .group_by("ym")
    )
    for r in res.all():
        if r.ym in buckets:
            buckets[r.ym]["revenue"] = round(float(r.rev or 0), 2)
            buckets[r.ym]["cogs"] = round(float(r.cogs or 0), 2)

    # OpEx query
    res2 = await db.execute(
        select(
            func.to_char(Expense.incurred_at, "YYYY-MM").label("ym"),
            func.coalesce(func.sum(Expense.amount), 0.0).label("opex"),
        )
        .where(Expense.incurred_at >= since)
        .group_by("ym")
    )
    for r in res2.all():
        if r.ym in buckets:
            buckets[r.ym]["opex"] = round(float(r.opex or 0), 2)

    # Net hesapla + sırala (eski → yeni)
    out = []
    for key in sorted(buckets.keys()):
        b = buckets[key]
        b["net"] = round(b["revenue"] - b["cogs"] - b["opex"], 2)
        out.append(b)
    return out


async def top_products_by_profit(
    db: AsyncSession, *, since_days: int = 30, limit: int = 10
) -> list[dict]:
    """En kârlı urunler (gelir × marj)."""
    since = datetime.utcnow() - timedelta(days=since_days)
    res = await db.execute(
        select(
            Product.id,
            Product.name,
            Product.unit,
            Product.cost,
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
            func.sum(OrderItem.quantity * Product.cost).label("cogs"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.status != OrderStatus.CANCELLED,
            Order.created_at >= since,
        )
        .group_by(Product.id, Product.name, Product.unit, Product.cost)
    )
    rows = res.all()
    out = []
    for r in rows:
        rev = float(r.revenue or 0)
        cogs = float(r.cogs or 0)
        profit = rev - cogs
        margin = (profit / rev * 100) if rev > 0 else 0.0
        out.append(
            {
                "product_id": r.id,
                "name": r.name,
                "unit": r.unit,
                "units_sold": float(r.units or 0),
                "revenue": round(rev, 2),
                "cogs": round(cogs, 2),
                "gross_profit": round(profit, 2),
                "gross_margin_pct": round(margin, 1),
            }
        )
    return sorted(out, key=lambda x: x["gross_profit"], reverse=True)[:limit]
