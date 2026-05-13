from collections import defaultdict
from datetime import datetime, timedelta
import math

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.crud import products as products_crud
from app.db.models import Order, OrderItem, OrderStatus, Product
from app.tools.base import AgentContext


async def check_product_availability(name: str, quantity: float, *, ctx: AgentContext) -> dict:
    matches = await products_crud.search_by_name(ctx.db, name, limit=5)
    if not matches:
        return {"available": False, "matches": [], "error": f"'{name}' adli urun bulamadim."}
    best = matches[0]
    return {
        "available": best.stock >= quantity,
        "product": {
            "id": best.id,
            "name": best.name,
            "unit": best.unit,
            "price": best.price,
            "stock": best.stock,
        },
        "alternatives": [{"id": m.id, "name": m.name} for m in matches[1:]],
    }


async def get_product_price(name: str, *, ctx: AgentContext) -> dict:
    matches = await products_crud.search_by_name(ctx.db, name, limit=3)
    if not matches:
        return {"error": f"'{name}' adli urun bulamadim."}
    best = matches[0]
    return {
        "product": best.name,
        "unit": best.unit,
        "price": best.price,
    }


async def _sales_velocity_by_product(ctx: AgentContext, days: int = 14) -> dict[int, dict]:
    since = datetime.utcnow() - timedelta(days=days)
    res = await ctx.db.execute(
        select(Order)
        .where(Order.created_at >= since)
        .where(Order.status != OrderStatus.CANCELLED)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    totals: dict[int, float] = defaultdict(float)
    for order in res.scalars():
        for item in order.items:
            totals[item.product_id] += float(item.quantity)
    return {
        product_id: {
            "sold_last_days": round(qty, 2),
            "avg_daily_sales": round(qty / max(days, 1), 2),
        }
        for product_id, qty in totals.items()
    }


def _stock_row(p: Product, velocity: dict | None = None) -> dict:
    velocity = velocity or {"sold_last_days": 0.0, "avg_daily_sales": 0.0}
    avg_daily = float(velocity.get("avg_daily_sales") or 0)
    days_left = round(float(p.stock) / avg_daily, 1) if avg_daily > 0 else None
    target_stock = max(float(p.low_stock_threshold) * 3, float(p.stock) + avg_daily * 10)
    suggested = max(0.0, target_stock - float(p.stock))
    if p.unit == "adet":
        suggested_reorder_qty = int(math.ceil(suggested))
    else:
        suggested_reorder_qty = round(suggested, 1)
    return {
        "id": p.id,
        "name": p.name,
        "unit": p.unit,
        "stock": p.stock,
        "low_stock_threshold": p.low_stock_threshold,
        "is_low": p.stock <= p.low_stock_threshold,
        "price": p.price,
        "sold_last_14_days": velocity.get("sold_last_days", 0.0),
        "avg_daily_sales": avg_daily,
        "estimated_days_left": days_left,
        "suggested_reorder_qty": suggested_reorder_qty,
    }


async def stock_overview(*, low_only: bool = False, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    products = await products_crud.list_all(ctx.db, low_stock_only=low_only)
    velocity = await _sales_velocity_by_product(ctx, days=14)
    rows = [_stock_row(p, velocity.get(p.id)) for p in products]
    rows.sort(key=lambda p: (not p["is_low"], p["estimated_days_left"] if p["estimated_days_left"] is not None else 9999, p["stock"]))
    return {
        "count": len(rows),
        "products": rows,
    }
