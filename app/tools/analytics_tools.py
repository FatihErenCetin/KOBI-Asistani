"""Panel AI asistani icin analitik tool sarmalayicilari."""

from app.db.crud import product_analytics
from app.db.crud import products as products_crud
from app.tools.base import AgentContext


async def low_margin_products(
    margin_threshold: float = 20, *, ctx: AgentContext
) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    rows = await product_analytics.low_margin_products(ctx.db, margin_threshold)
    return {"threshold": margin_threshold, "count": len(rows), "products": rows}


async def fast_depleting(max_days: float = 7, *, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    rows = await product_analytics.fast_depleting_products(ctx.db, max_days)
    return {"max_days": max_days, "count": len(rows), "products": rows}


async def supplier_performance(*, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    rows = await product_analytics.supplier_lead_time_stats(ctx.db)
    return {"suppliers": rows}


async def product_analytics_report(product_id: int, *, ctx: AgentContext) -> dict:
    """Tek urun icin 30g/7g sat, gunluk hiz, kac gunluk stok, kar marji."""
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    p = await products_crud.get_by_id(ctx.db, product_id)
    if p is None:
        return {"error": f"#{product_id} urun bulunamadi."}
    data = await product_analytics.for_product(ctx.db, p)
    return {
        "product": {
            "id": p.id,
            "name": p.name,
            "unit": p.unit,
            "stock": p.stock,
            "price": p.price,
            "cost": p.cost,
        },
        "analytics": data,
    }


async def category_stock(*, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    rows = await product_analytics.category_stock_overview(ctx.db)
    return {"categories": rows}
