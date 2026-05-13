from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.db.crud import stock_balances as balances_crud
from app.db.models import AdminUser, Product, StockMovement, StockMovementReason


async def record(
    db: AsyncSession,
    *,
    product: Product,
    delta: float,
    reason: StockMovementReason,
    warehouse_id: int | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    note: str | None = None,
    admin_id: int | None = None,
) -> StockMovement:
    """Stok hareketini yazar VE Product.stock + StockBalance'i guncellr.

    warehouse_id verilmezse default depo kullanilir. Tek atomik nokta:
    - StockBalance.quantity += delta (per-warehouse)
    - Product.stock recompute (denormalize cache = SUM(balances))
    - StockMovement satiri yazilir (audit + balance_after)
    """
    if warehouse_id is None:
        default = await balances_crud.get_default_warehouse(db)
        warehouse_id = default.id if default else 1

    # Lazy sync: Product.stock dogrudan set edilmis (test/migration) ama balance yoksa,
    # cache farkini default warehouse'a getir ki kasit kaybolmasin.
    current_total = await balances_crud.total_for_product(db, product.id)
    if product.stock > current_total:
        diff = product.stock - current_total
        default_w = await balances_crud.get_default_warehouse(db)
        sync_wh = default_w.id if default_w else warehouse_id
        await balances_crud.adjust(db, product.id, sync_wh, diff)

    # Per-warehouse balance update
    new_warehouse_qty = await balances_crud.adjust(
        db, product.id, warehouse_id, delta
    )
    # Product.stock denormalize cache recompute (sum of all balances)
    product.stock = await balances_crud.total_for_product(db, product.id)

    row = StockMovement(
        product_id=product.id,
        warehouse_id=warehouse_id,
        delta=delta,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        note=note,
        balance_after=new_warehouse_qty,  # per-warehouse balance after
        created_by_admin_id=admin_id,
    )
    db.add(row)
    await db.flush()
    return row


async def list_for_product(
    db: AsyncSession, product_id: int, limit: int = 100
) -> list[StockMovement]:
    res = await db.execute(
        select(StockMovement)
        .where(StockMovement.product_id == product_id)
        .order_by(desc(StockMovement.created_at))
        .limit(limit)
    )
    return list(res.scalars())


async def list_for_product_with_admin(
    db: AsyncSession, product_id: int, limit: int = 100
) -> list[tuple[StockMovement, str | None]]:
    """JOIN AdminUser ile (row, admin_name) doner. Endpoint icin."""
    a = aliased(AdminUser)
    res = await db.execute(
        select(StockMovement, a.name)
        .outerjoin(a, StockMovement.created_by_admin_id == a.id)
        .where(StockMovement.product_id == product_id)
        .order_by(desc(StockMovement.created_at))
        .limit(limit)
    )
    return [(row, name) for row, name in res.all()]
