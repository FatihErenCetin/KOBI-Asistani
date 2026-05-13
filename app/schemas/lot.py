from datetime import date, datetime

from pydantic import BaseModel


class StockLotCreate(BaseModel):
    warehouse_id: int
    lot_number: str
    quantity: float
    expiry_date: date | None = None
    supplier_id: int | None = None
    note: str | None = None


class StockLotOut(BaseModel):
    id: int
    product_id: int
    warehouse_id: int
    warehouse_name: str | None = None
    lot_number: str
    quantity: float
    expiry_date: date | None
    supplier_id: int | None
    supplier_name: str | None = None
    received_at: datetime
    note: str | None


class ExpiringLotRow(BaseModel):
    lot_id: int
    product_id: int
    product_name: str
    lot_number: str
    expiry_date: date
    days_left: int
    quantity: float
