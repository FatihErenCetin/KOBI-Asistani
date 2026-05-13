from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ProductSupplier, Supplier


async def get_by_id(db: AsyncSession, supplier_id: int) -> Supplier | None:
    res = await db.execute(
        select(Supplier)
        .where(Supplier.id == supplier_id)
        .options(selectinload(Supplier.product_links).selectinload(ProductSupplier.product))
    )
    return res.scalar_one_or_none()


async def list_all(
    db: AsyncSession,
    search: str | None = None,
    include_inactive: bool = False,
) -> list[Supplier]:
    stmt = select(Supplier)
    if not include_inactive:
        stmt = stmt.where(Supplier.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Supplier.name.ilike(pattern),
                Supplier.contact_name.ilike(pattern),
                Supplier.phone.ilike(pattern),
            )
        )
    res = await db.execute(stmt.order_by(Supplier.name))
    return list(res.scalars())


async def create(
    db: AsyncSession,
    *,
    name: str,
    contact_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> Supplier:
    s = Supplier(
        name=name,
        contact_name=contact_name,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
        is_active=True,
    )
    db.add(s)
    await db.flush()
    return s


async def update(db: AsyncSession, supplier: Supplier, **fields) -> Supplier:
    for k, v in fields.items():
        if v is not None and hasattr(supplier, k):
            setattr(supplier, k, v)
    supplier.updated_at = datetime.utcnow()
    await db.flush()
    return supplier


async def soft_delete(db: AsyncSession, supplier: Supplier) -> Supplier:
    supplier.is_active = False
    await db.flush()
    return supplier


async def count_linked_products(db: AsyncSession, supplier_id: int) -> int:
    res = await db.execute(
        select(func.count(ProductSupplier.id)).where(
            ProductSupplier.supplier_id == supplier_id
        )
    )
    return int(res.scalar_one())
