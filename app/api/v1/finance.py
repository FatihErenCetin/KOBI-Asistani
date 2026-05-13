"""Finansal analiz + Expense CRUD endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_optional, get_db, require_admin
from app.db.crud import expenses as expenses_crud
from app.db.crud import financial_analytics as fin_analytics
from app.db.models import AdminUser, Expense, ExpenseCategory
from app.schemas.finance import (
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    PeriodSummary,
)

router = APIRouter(
    prefix="/finance", tags=["finance"], dependencies=[Depends(require_admin)]
)


def _to_out(e: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=e.id,
        category=e.category.value,
        amount=e.amount,
        vendor=e.vendor,
        description=e.description,
        incurred_at=e.incurred_at,
        is_recurring=e.is_recurring,
        created_at=e.created_at,
    )


def _parse_category(value: str) -> ExpenseCategory:
    try:
        return ExpenseCategory(value.lower())
    except ValueError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Bilinmeyen kategori: {value}"
        ) from e


# ---------- Analytics endpoints ----------


@router.get("/summary", response_model=PeriodSummary)
async def get_period_summary(
    since_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Son N gun finansal ozet (gelir, COGS, brut kar, opex, net kar + delta %)."""
    return await fin_analytics.period_summary(db, since_days=since_days)


@router.get("/monthly-trend", response_model=list[dict])
async def get_monthly_trend(
    months: int = Query(default=6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    """Son N ayin aylik bazda revenue/cogs/opex/net trendi."""
    return await fin_analytics.monthly_trend(db, months=months)


@router.get("/category-breakdown", response_model=list[dict])
async def get_category_breakdown(
    since_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Gider kategorilerinin dagilimi (% pay + tutar)."""
    return await fin_analytics.category_breakdown(db, since_days=since_days)


@router.get("/top-products", response_model=list[dict])
async def get_top_products(
    since_days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """En karli urunler (brut kar bazli)."""
    return await fin_analytics.top_products_by_profit(
        db, since_days=since_days, limit=limit
    )


# ---------- Expense CRUD ----------


@router.get("/expenses", response_model=list[ExpenseOut])
async def list_expenses(
    since_days: int | None = Query(default=None, ge=1, le=365),
    category: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timedelta

    since = (
        datetime.utcnow() - timedelta(days=since_days) if since_days else None
    )
    cat = _parse_category(category) if category else None
    rows = await expenses_crud.list_all(
        db, since=since, category=cat, limit=limit
    )
    return [_to_out(e) for e in rows]


@router.post(
    "/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED
)
async def create_expense(
    payload: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    cat = _parse_category(payload.category)
    admin_id = current_admin.id if current_admin else None
    e = await expenses_crud.create(
        db,
        category=cat,
        amount=payload.amount,
        vendor=payload.vendor,
        description=payload.description,
        incurred_at=payload.incurred_at,
        is_recurring=payload.is_recurring,
        admin_id=admin_id,
    )
    await db.commit()
    return _to_out(e)


@router.patch("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
):
    e = await expenses_crud.get_by_id(db, expense_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    fields = payload.model_dump(exclude_unset=True)
    if "category" in fields and fields["category"] is not None:
        fields["category"] = _parse_category(fields["category"])
    await expenses_crud.update(db, e, **fields)
    await db.commit()
    return _to_out(e)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, db: AsyncSession = Depends(get_db)):
    e = await expenses_crud.get_by_id(db, expense_id)
    if e is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Expense not found")
    await expenses_crud.delete(db, e)
    await db.commit()
