from datetime import datetime

from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    category: str
    amount: float
    vendor: str | None = None
    description: str | None = None
    incurred_at: datetime | None = None
    is_recurring: bool = False


class ExpenseUpdate(BaseModel):
    category: str | None = None
    amount: float | None = None
    vendor: str | None = None
    description: str | None = None
    incurred_at: datetime | None = None
    is_recurring: bool | None = None


class ExpenseOut(BaseModel):
    id: int
    category: str
    amount: float
    vendor: str | None
    description: str | None
    incurred_at: datetime
    is_recurring: bool
    created_at: datetime


class PeriodSummary(BaseModel):
    since: str
    until: str
    since_days: int
    revenue: float
    cogs: float
    gross_profit: float
    operating_expenses: float
    net_profit: float
    gross_margin_pct: float
    net_margin_pct: float
    prev_revenue: float
    prev_net_profit: float
    revenue_change_pct: float | None
    net_profit_change_pct: float | None
