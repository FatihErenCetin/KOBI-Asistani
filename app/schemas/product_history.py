from datetime import datetime

from pydantic import BaseModel


class PriceHistoryRow(BaseModel):
    id: int
    field: str
    old_value: float | None
    new_value: float
    reason: str | None
    changed_at: datetime
    changed_by_admin_id: int | None
    changed_by_admin_name: str | None = None


class StockMovementRow(BaseModel):
    id: int
    delta: float
    reason: str
    reference_type: str | None
    reference_id: int | None
    note: str | None
    balance_after: float
    created_at: datetime
    created_by_admin_id: int | None
    created_by_admin_name: str | None = None


class SparklinePoint(BaseModel):
    day: str
    units: float


class ProductAnalytics(BaseModel):
    units_sold_30d: float
    revenue_30d: float
    units_sold_7d: float
    daily_velocity: float
    days_of_stock: float | None
    profit_margin_pct: float | None
    last_sale_at: str | None
