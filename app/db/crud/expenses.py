from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Expense, ExpenseCategory


async def create(
    db: AsyncSession,
    *,
    category: ExpenseCategory,
    amount: float,
    vendor: str | None = None,
    description: str | None = None,
    incurred_at: datetime | None = None,
    is_recurring: bool = False,
    admin_id: int | None = None,
) -> Expense:
    e = Expense(
        category=category,
        amount=amount,
        vendor=vendor,
        description=description,
        incurred_at=incurred_at or datetime.utcnow(),
        is_recurring=is_recurring,
        created_by_admin_id=admin_id,
    )
    db.add(e)
    await db.flush()
    return e


async def get_by_id(db: AsyncSession, expense_id: int) -> Expense | None:
    return await db.get(Expense, expense_id)


async def list_all(
    db: AsyncSession,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    category: ExpenseCategory | None = None,
    limit: int = 200,
) -> list[Expense]:
    stmt = select(Expense)
    if since is not None:
        stmt = stmt.where(Expense.incurred_at >= since)
    if until is not None:
        stmt = stmt.where(Expense.incurred_at <= until)
    if category is not None:
        stmt = stmt.where(Expense.category == category)
    stmt = stmt.order_by(desc(Expense.incurred_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars())


async def update(db: AsyncSession, expense: Expense, **fields) -> Expense:
    for k, v in fields.items():
        if v is not None and hasattr(expense, k):
            setattr(expense, k, v)
    await db.flush()
    return expense


async def delete(db: AsyncSession, expense: Expense) -> None:
    await db.delete(expense)
    await db.flush()
