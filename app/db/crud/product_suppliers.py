from datetime import datetime

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ProductSupplier


async def list_for_product(db: AsyncSession, product_id: int) -> list[ProductSupplier]:
    res = await db.execute(
        select(ProductSupplier)
        .where(ProductSupplier.product_id == product_id)
        .options(selectinload(ProductSupplier.supplier))
        .order_by(ProductSupplier.is_preferred.desc(), ProductSupplier.id)
    )
    return list(res.scalars())


async def get_link(
    db: AsyncSession, product_id: int, supplier_id: int
) -> ProductSupplier | None:
    res = await db.execute(
        select(ProductSupplier)
        .where(
            ProductSupplier.product_id == product_id,
            ProductSupplier.supplier_id == supplier_id,
        )
        .options(selectinload(ProductSupplier.supplier))
    )
    return res.scalar_one_or_none()


async def add_link(
    db: AsyncSession,
    *,
    product_id: int,
    supplier_id: int,
    supplier_sku: str | None = None,
    last_unit_cost: float | None = None,
    lead_time_days: int | None = None,
    is_preferred: bool = False,
    notes: str | None = None,
) -> ProductSupplier:
    if is_preferred:
        await db.execute(
            sa_update(ProductSupplier)
            .where(ProductSupplier.product_id == product_id)
            .values(is_preferred=False)
        )
    link = ProductSupplier(
        product_id=product_id,
        supplier_id=supplier_id,
        supplier_sku=supplier_sku,
        last_unit_cost=last_unit_cost,
        last_purchase_at=datetime.utcnow() if last_unit_cost is not None else None,
        lead_time_days=lead_time_days,
        is_preferred=is_preferred,
        notes=notes,
    )
    db.add(link)
    await db.flush()
    return link


async def update_link(
    db: AsyncSession, link: ProductSupplier, **fields
) -> ProductSupplier:
    if fields.get("is_preferred") is True and not link.is_preferred:
        await db.execute(
            sa_update(ProductSupplier)
            .where(ProductSupplier.product_id == link.product_id)
            .values(is_preferred=False)
        )
    for k, v in fields.items():
        if v is not None and hasattr(link, k):
            setattr(link, k, v)
    if fields.get("last_unit_cost") is not None:
        link.last_purchase_at = datetime.utcnow()
    await db.flush()
    return link


async def remove_link(db: AsyncSession, link: ProductSupplier) -> None:
    await db.delete(link)
    await db.flush()
