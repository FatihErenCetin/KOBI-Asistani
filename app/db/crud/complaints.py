from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CustomerComplaint


async def create(
    db: AsyncSession,
    *,
    customer_id: int | None,
    telegram_user_id: int | None,
    message_text: str,
    risk_score: float,
    signals: list[str],
) -> CustomerComplaint:
    c = CustomerComplaint(
        customer_id=customer_id,
        telegram_user_id=telegram_user_id,
        message_text=message_text[:1900],
        risk_score=risk_score,
        signals=",".join(signals)[:280] if signals else None,
    )
    db.add(c)
    await db.flush()
    return c


async def list_open(db: AsyncSession, limit: int = 50) -> list[CustomerComplaint]:
    res = await db.execute(
        select(CustomerComplaint)
        .where(CustomerComplaint.resolved.is_(False))
        .order_by(desc(CustomerComplaint.created_at))
        .limit(limit)
    )
    return list(res.scalars())


async def get_by_id(db: AsyncSession, cid: int) -> CustomerComplaint | None:
    return await db.get(CustomerComplaint, cid)


async def mark_resolved(db: AsyncSession, complaint: CustomerComplaint) -> CustomerComplaint:
    complaint.resolved = True
    await db.flush()
    return complaint
