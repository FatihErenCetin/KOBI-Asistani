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
    """Reactive kayit: Telegram mesajindan tetiklenen sikayet sinyali."""
    subject = (message_text or "Şikayet sinyali")[:80]
    c = CustomerComplaint(
        customer_id=customer_id,
        telegram_user_id=telegram_user_id,
        subject=subject,
        description=None,
        message_text=(message_text or "")[:1900],
        risk_score=risk_score,
        signals=",".join(signals)[:280] if signals else None,
        source="telegram_message",
        auto_generated=False,
    )
    db.add(c)
    await db.flush()
    return c


async def create_auto(
    db: AsyncSession,
    *,
    customer_id: int | None,
    subject: str,
    description: str | None,
    risk_score: float,
    source: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
    signals: list[str] | None = None,
) -> CustomerComplaint:
    """Proactive kayit: agentic risk scanner tarafindan otomatik yazilan kayit."""
    c = CustomerComplaint(
        customer_id=customer_id,
        telegram_user_id=None,
        subject=subject[:200],
        description=description[:1900] if description else None,
        message_text=None,
        risk_score=risk_score,
        signals=",".join(signals)[:280] if signals else None,
        source=source,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        auto_generated=True,
    )
    db.add(c)
    await db.flush()
    return c


async def list_open(db: AsyncSession, limit: int = 100) -> list[CustomerComplaint]:
    res = await db.execute(
        select(CustomerComplaint)
        .where(CustomerComplaint.resolved.is_(False))
        .order_by(desc(CustomerComplaint.created_at))
        .limit(limit)
    )
    return list(res.scalars())


async def get_by_id(db: AsyncSession, cid: int) -> CustomerComplaint | None:
    return await db.get(CustomerComplaint, cid)


async def mark_resolved(
    db: AsyncSession, complaint: CustomerComplaint
) -> CustomerComplaint:
    complaint.resolved = True
    await db.flush()
    return complaint
