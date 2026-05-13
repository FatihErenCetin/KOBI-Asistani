from datetime import datetime

from pydantic import BaseModel


class SupplierBase(BaseModel):
    name: str
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None


class SupplierOut(SupplierBase):
    id: int
    is_active: bool
    created_at: datetime
    linked_product_count: int = 0


class ProductSupplierLinkIn(BaseModel):
    supplier_id: int
    supplier_sku: str | None = None
    last_unit_cost: float | None = None
    lead_time_days: int | None = None
    is_preferred: bool = False
    notes: str | None = None


class ProductSupplierLinkUpdate(BaseModel):
    supplier_sku: str | None = None
    last_unit_cost: float | None = None
    lead_time_days: int | None = None
    is_preferred: bool | None = None
    notes: str | None = None


class ProductSupplierLinkOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    supplier_sku: str | None
    last_unit_cost: float | None
    last_purchase_at: datetime | None
    lead_time_days: int | None
    is_preferred: bool
    notes: str | None
