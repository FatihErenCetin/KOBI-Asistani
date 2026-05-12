from app.db.crud import products as products_crud
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


async def stock_overview(*, low_only: bool = False, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    products = await products_crud.list_all(ctx.db, low_stock_only=low_only)
    return {
        "count": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "unit": p.unit,
                "stock": p.stock,
                "low_stock_threshold": p.low_stock_threshold,
                "is_low": p.stock <= p.low_stock_threshold,
                "price": p.price,
            }
            for p in products
        ],
    }
