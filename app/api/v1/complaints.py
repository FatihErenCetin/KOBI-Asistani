from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import complaints as complaints_crud

router = APIRouter(
    prefix="/complaints", tags=["complaints"], dependencies=[Depends(require_admin)]
)


def _to_dict(c) -> dict:
    return {
        "id": c.id,
        "customer_id": c.customer_id,
        "telegram_user_id": c.telegram_user_id,
        "message_text": c.message_text,
        "risk_score": c.risk_score,
        "signals": c.signals.split(",") if c.signals else [],
        "resolved": c.resolved,
        "created_at": c.created_at.isoformat(),
    }


@router.get("", response_model=list[dict])
async def list_open_complaints(db: AsyncSession = Depends(get_db)):
    rows = await complaints_crud.list_open(db)
    return [_to_dict(r) for r in rows]


@router.post("/{complaint_id}/resolve", response_model=dict)
async def resolve_complaint(complaint_id: int, db: AsyncSession = Depends(get_db)):
    c = await complaints_crud.get_by_id(db, complaint_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    await complaints_crud.mark_resolved(db, c)
    await db.commit()
    return _to_dict(c)
