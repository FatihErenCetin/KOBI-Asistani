"""SKT yaklasan lot'lar icin AI advisor agent endpoint'leri."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import stock_lots as lots_crud
from app.db.models import LotAction, LotActionStatus
from app.services import expiry_advisor

router = APIRouter(
    prefix="/lot-actions",
    tags=["lot-actions"],
    dependencies=[Depends(require_admin)],
)


def _to_dict(a: LotAction) -> dict:
    return {
        "id": a.id,
        "lot_id": a.lot_id,
        "action_type": a.action_type.value,
        "subject": a.subject,
        "description": a.description,
        "suggested_discount_pct": a.suggested_discount_pct,
        "priority": a.priority,
        "status": a.status.value,
        "created_at": a.created_at.isoformat(),
        "applied_at": a.applied_at.isoformat() if a.applied_at else None,
    }


@router.post("/analyze", response_model=dict)
async def analyze_expiring(
    within_days: int = Query(default=14, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Tum yaklasan SKT lot'lari icin AI oneri uret. Idempotent: pending oneri
    olan lot'lar atlanir."""
    return await expiry_advisor.analyze_all_expiring(db, within_days=within_days)


@router.post("/lots/{lot_id}/analyze", response_model=list[dict])
async def analyze_single_lot(
    lot_id: int,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Tek lot icin oneri uret. force=true ise mevcut pending oneriler de
    silinmeden ekstra oneriler eklenebilir."""
    lots = await lots_crud.list_for_product(db, 0)  # boş çağrı sadece import için
    # Doğrudan lookup
    from sqlalchemy import select

    from app.db.models import StockLot

    res = await db.execute(select(StockLot).where(StockLot.id == lot_id))
    lot = res.scalar_one_or_none()
    if lot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lot not found")
    # product/warehouse lazy load için tekrar yükle (selectinload eksik)
    from sqlalchemy.orm import selectinload

    res = await db.execute(
        select(StockLot)
        .where(StockLot.id == lot_id)
        .options(selectinload(StockLot.product), selectinload(StockLot.warehouse))
    )
    lot = res.scalar_one()
    actions = await expiry_advisor.analyze_lot(db, lot, force=force)
    await db.commit()
    return [_to_dict(a) for a in actions]


@router.get("/lots/{lot_id}", response_model=list[dict])
async def list_for_lot(lot_id: int, db: AsyncSession = Depends(get_db)):
    actions = await expiry_advisor.list_actions_for_lot(db, lot_id)
    return [_to_dict(a) for a in actions]


@router.get("", response_model=list[dict])
async def list_pending(db: AsyncSession = Depends(get_db)):
    """Tum acik (pending) onerileri listele — dashboard icin."""
    actions = await expiry_advisor.list_all_pending(db)
    return [_to_dict(a) for a in actions]


@router.post("/{action_id}/apply", response_model=dict)
async def apply_action(action_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(LotAction, action_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Action not found")
    await expiry_advisor.update_status(db, a, LotActionStatus.APPLIED)
    await db.commit()
    return _to_dict(a)


@router.post("/{action_id}/dismiss", response_model=dict)
async def dismiss_action(action_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(LotAction, action_id)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Action not found")
    await expiry_advisor.update_status(db, a, LotActionStatus.DISMISSED)
    await db.commit()
    return _to_dict(a)
