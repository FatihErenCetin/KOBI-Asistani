from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Customer


async def get_by_id(db: AsyncSession, customer_id: int) -> Customer | None:
    return await db.get(Customer, customer_id)


async def get_by_telegram(db: AsyncSession, telegram_user_id: int) -> Customer | None:
    res = await db.execute(
        select(Customer).where(Customer.telegram_user_id == telegram_user_id)
    )
    return res.scalar_one_or_none()


async def get_by_phone(db: AsyncSession, phone: str) -> Customer | None:
    res = await db.execute(select(Customer).where(Customer.phone == phone))
    return res.scalar_one_or_none()


async def search(db: AsyncSession, q: str, limit: int = 20) -> list[Customer]:
    pattern = f"%{q}%"
    res = await db.execute(
        select(Customer)
        .where(or_(Customer.name.ilike(pattern), Customer.phone.ilike(pattern)))
        .limit(limit)
    )
    return list(res.scalars())


async def create(
    db: AsyncSession,
    name: str,
    phone: str | None = None,
    telegram_user_id: int | None = None,
) -> Customer:
    c = Customer(name=name, phone=phone, telegram_user_id=telegram_user_id)
    db.add(c)
    await db.flush()
    return c


async def link_telegram(db: AsyncSession, customer: Customer, telegram_user_id: int) -> Customer:
    customer.telegram_user_id = telegram_user_id
    await db.flush()
    return customer
