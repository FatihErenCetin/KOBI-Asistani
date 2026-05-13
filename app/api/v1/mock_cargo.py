from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.db.models import Shipment
from app.integrations import cargo_mock
from app.services import shipment_notifier

router = APIRouter(prefix="/mock-cargo", tags=["mock-cargo"])


@router.get("/{tracking_no}")
async def get_status(tracking_no: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Shipment).where(Shipment.tracking_no == tracking_no)
    )
    s = res.scalar_one_or_none()
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipment not found")
    return cargo_mock.get_status_summary(s)


@router.post("/{tracking_no}/advance")
async def advance_status(tracking_no: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Shipment)
        .where(Shipment.tracking_no == tracking_no)
        .options(selectinload(Shipment.order))
    )
    s = res.scalar_one_or_none()
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shipment not found")
    old_status = s.status
    await cargo_mock.advance(db, s)
    new_status = s.status
    await db.commit()
    if new_status != old_status:
        await shipment_notifier.notify_status_change(db, s, new_status)
    return cargo_mock.get_status_summary(s)
