"""Lot/batch ve FIFO tüketim helper'lari.

FIFO sirasi: en yakin expiry_date once (NULL expiry en sona), sonra received_at
artan. Bu, gida isletmesinde son kullanma yaklaşan lot'larin once cikmasini
saglar.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import StockLot


class InsufficientStock(Exception):
    """Lot'lardan tuketilen miktar yetersiz."""


async def list_for_product(
    db: AsyncSession,
    product_id: int,
    *,
    warehouse_id: int | None = None,
    only_with_stock: bool = True,
) -> list[StockLot]:
    stmt = (
        select(StockLot)
        .where(StockLot.product_id == product_id)
        .options(selectinload(StockLot.warehouse), selectinload(StockLot.supplier))
        .order_by(
            StockLot.expiry_date.asc().nulls_last(),
            StockLot.received_at.asc(),
        )
    )
    if warehouse_id is not None:
        stmt = stmt.where(StockLot.warehouse_id == warehouse_id)
    if only_with_stock:
        stmt = stmt.where(StockLot.quantity > 0)
    res = await db.execute(stmt)
    return list(res.scalars())


async def create(
    db: AsyncSession,
    *,
    product_id: int,
    warehouse_id: int,
    lot_number: str,
    quantity: float,
    expiry_date: date | None = None,
    supplier_id: int | None = None,
    received_at: datetime | None = None,
    note: str | None = None,
) -> StockLot:
    lot = StockLot(
        product_id=product_id,
        warehouse_id=warehouse_id,
        lot_number=lot_number,
        quantity=quantity,
        expiry_date=expiry_date,
        supplier_id=supplier_id,
        received_at=received_at or datetime.utcnow(),
        note=note,
    )
    db.add(lot)
    await db.flush()
    return lot


async def consume_fifo(
    db: AsyncSession,
    *,
    product_id: int,
    warehouse_id: int,
    qty: float,
) -> list[tuple[StockLot, float]]:
    """En eski lot'tan baslayarak qty kadar tuketir.

    Returns: [(lot, consumed_amount), ...]
    Raises: InsufficientStock — toplam lot stoğu istenenden az ise.

    Not: Lot olmayan urunlerde (lazy migration) bos liste doner — caller
    StockBalance üzerinden devam etmelidir.
    """
    lots = await list_for_product(
        db, product_id, warehouse_id=warehouse_id, only_with_stock=True
    )
    if not lots:
        return []  # caller fallback to plain balance adjustment

    consumed: list[tuple[StockLot, float]] = []
    remaining = qty
    for lot in lots:
        if remaining <= 0:
            break
        take = min(remaining, lot.quantity)
        lot.quantity -= take
        remaining -= take
        consumed.append((lot, take))
    if remaining > 0:
        raise InsufficientStock(
            f"Lot stoğu yetersiz: {remaining} {qty} eksik"
        )
    await db.flush()
    return consumed


async def expiring_soon(
    db: AsyncSession, within_days: int = 14
) -> list[StockLot]:
    """Onumuzdeki N gun icinde sona erecek aktif lot'lar."""
    today = date.today()
    cutoff = today + timedelta(days=within_days)
    res = await db.execute(
        select(StockLot)
        .where(
            StockLot.quantity > 0,
            StockLot.expiry_date.is_not(None),
            StockLot.expiry_date <= cutoff,
            StockLot.expiry_date >= today,
        )
        .options(selectinload(StockLot.product))
        .order_by(StockLot.expiry_date.asc())
    )
    return list(res.scalars())
