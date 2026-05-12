from datetime import date, datetime

from pydantic import BaseModel


class SummaryStats(BaseModel):
    orders_last_24h: int
    revenue_last_24h: float
    orders_vs_yesterday_pct: float
    pending_to_prepare: int
    urgent_today: int
    shipments_today: int
    low_stock_count: int


class PendingOrderRow(BaseModel):
    id: int
    customer_name: str
    total: float
    status: str
    created_at: datetime
    promised_delivery: date | None


class LowStockRow(BaseModel):
    id: int
    name: str
    stock: float
    low_stock_threshold: float
    unit: str


class ShipmentTodayRow(BaseModel):
    order_id: int
    tracking_no: str
    customer_name: str
    status: str
    current_location: str | None
    eta: date | None


class DashboardToday(BaseModel):
    summary: SummaryStats
    pending_orders: list[PendingOrderRow]
    todays_shipments: list[ShipmentTodayRow]
    low_stock_items: list[LowStockRow]
    recent_orders: list[PendingOrderRow]
