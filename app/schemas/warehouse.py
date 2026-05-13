from datetime import datetime

from pydantic import BaseModel


class WarehouseBase(BaseModel):
    name: str
    code: str | None = None
    address: str | None = None
    is_default: bool = False


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    address: str | None = None
    is_default: bool | None = None


class WarehouseOut(WarehouseBase):
    id: int
    is_active: bool
    created_at: datetime


class WarehouseStockRow(BaseModel):
    warehouse_id: int
    warehouse_name: str
    quantity: float
