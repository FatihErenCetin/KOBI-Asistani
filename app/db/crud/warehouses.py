from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Warehouse


async def get_by_id(db: AsyncSession, warehouse_id: int) -> Warehouse | None:
    return await db.get(Warehouse, warehouse_id)


async def list_all(
    db: AsyncSession,
    search: str | None = None,
    include_inactive: bool = False,
) -> list[Warehouse]:
    stmt = select(Warehouse)
    if not include_inactive:
        stmt = stmt.where(Warehouse.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(Warehouse.name.ilike(pattern), Warehouse.code.ilike(pattern))
        )
    res = await db.execute(stmt.order_by(Warehouse.is_default.desc(), Warehouse.name))
    return list(res.scalars())


async def create(
    db: AsyncSession,
    *,
    name: str,
    code: str | None = None,
    address: str | None = None,
    is_default: bool = False,
) -> Warehouse:
    # is_default=True ise diger default'u kapat
    if is_default:
        res = await db.execute(
            select(Warehouse).where(Warehouse.is_default.is_(True))
        )
        for w in res.scalars():
            w.is_default = False
    w = Warehouse(
        name=name, code=code, address=address, is_default=is_default, is_active=True
    )
    db.add(w)
    await db.flush()
    return w


async def update(db: AsyncSession, warehouse: Warehouse, **fields) -> Warehouse:
    if fields.get("is_default") is True and not warehouse.is_default:
        res = await db.execute(
            select(Warehouse).where(Warehouse.is_default.is_(True))
        )
        for w in res.scalars():
            w.is_default = False
    for k, v in fields.items():
        if v is not None and hasattr(warehouse, k):
            setattr(warehouse, k, v)
    await db.flush()
    return warehouse


async def soft_delete(db: AsyncSession, warehouse: Warehouse) -> Warehouse:
    if warehouse.is_default:
        raise ValueError("Ana depo silinemez")
    warehouse.is_active = False
    await db.flush()
    return warehouse
