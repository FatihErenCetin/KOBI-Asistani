from datetime import date, datetime

from pydantic import BaseModel


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: float
    unit_price: float


class ShipmentOut(BaseModel):
    tracking_no: str
    carrier: str
    status: str
    current_location: str | None
    estimated_delivery: date | None


class CustomerSummary(BaseModel):
    id: int
    name: str
    phone: str | None


class OrderOut(BaseModel):
    id: int
    status: str
    total: float
    created_at: datetime
    promised_delivery: date | None
    note: str | None
    customer: CustomerSummary
    items: list[OrderItemOut]
    shipment: ShipmentOut | None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderCreate(BaseModel):
    customer_id: int
    items: list[dict]
    note: str | None = None
