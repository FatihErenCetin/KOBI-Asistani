from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)


async def search_by_name(db: AsyncSession, query: str, limit: int = 10) -> list[Product]:
    """Ad ve alias'larda case-insensitive arama."""
    pattern = f"%{query.lower()}%"
    res = await db.execute(
        select(Product)
        .where(or_(Product.name.ilike(pattern), Product.aliases.ilike(pattern)))
        .limit(limit)
    )
    return list(res.scalars())


async def list_all(
    db: AsyncSession, low_stock_only: bool = False, search: str | None = None
) -> list[Product]:
    stmt = select(Product)
    if low_stock_only:
        stmt = stmt.where(Product.stock <= Product.low_stock_threshold)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Product.name.ilike(pattern), Product.aliases.ilike(pattern)))
    res = await db.execute(stmt.order_by(Product.name))
    return list(res.scalars())


async def adjust_stock(db: AsyncSession, product: Product, delta: float) -> Product:
    product.stock = max(0.0, product.stock + delta)
    await db.flush()
    return product


async def set_stock(db: AsyncSession, product: Product, new_stock: float) -> Product:
    product.stock = max(0.0, new_stock)
    await db.flush()
    return product
