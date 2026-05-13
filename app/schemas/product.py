from datetime import datetime

from pydantic import BaseModel

from app.schemas.product_history import ProductAnalytics
from app.schemas.supplier import ProductSupplierLinkOut


class ProductOut(BaseModel):
    id: int
    name: str
    aliases: str | None
    unit: str
    price: float
    cost: float = 0
    stock: float
    low_stock_threshold: float
    description: str | None
    barcode: str | None = None
    category: str | None = None
    is_active: bool = True
    is_low: bool
    profit_margin_pct: float | None = None


class StockUpdate(BaseModel):
    stock: float


class ProductCreate(BaseModel):
    name: str
    unit: str
    price: float
    cost: float = 0
    stock: float = 0
    low_stock_threshold: float = 0
    aliases: str | None = None
    description: str | None = None
    barcode: str | None = None
    category: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    price: float | None = None
    cost: float | None = None
    low_stock_threshold: float | None = None
    aliases: str | None = None
    description: str | None = None
    barcode: str | None = None
    category: str | None = None
    reason: str | None = None


class StockAdjust(BaseModel):
    delta: float
    reason: str  # purchase|adjustment|return|waste
    note: str | None = None
    warehouse_id: int | None = None


class ProductOutDetailed(ProductOut):
    created_at: datetime
    updated_at: datetime
    suppliers: list[ProductSupplierLinkOut] = []
    analytics: ProductAnalytics | None = None
