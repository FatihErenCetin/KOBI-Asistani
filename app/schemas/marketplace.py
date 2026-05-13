"""Marketplace API şemaları."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class SupplierMarketplaceOut(BaseModel):
    id: int
    name: str
    category: str | None
    carrier: str | None
    city: str | None
    district: str | None
    description: str | None
    rating: float | None
    contact_name: str | None
    phone: str | None
    email: str | None
    last_used_at: datetime | None = None
    linked_product_count: int = 0


class RecentSupplierOut(BaseModel):
    supplier: SupplierMarketplaceOut
    last_used_at: datetime


class PurchaseOrderItemIn(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_cost: float = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    items: list[PurchaseOrderItemIn] = Field(min_length=1)
    expected_delivery: date | None = None
    notes: str | None = None
    # AI önerisinden geliyorsa bağlantı:
    recommendation_id: int | None = None


class PurchaseOrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_unit: str
    quantity: float
    unit_cost: float
    line_total: float


class PurchaseOrderOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    status: str
    total_cost: float
    expected_delivery: date | None
    received_at: datetime | None
    notes: str | None
    ai_suggested: bool
    suggestion_reason: str | None
    items: list[PurchaseOrderItemOut]
    created_at: datetime


class PurchaseOrderStatusUpdate(BaseModel):
    status: str  # draft|sent|confirmed|received|cancelled


class NearbyShopOut(BaseModel):
    id: int
    name: str
    shop_type: str | None
    city: str
    district: str | None
    distance_km: float | None
    preferred_carrier: str | None


class NearbySignalOut(BaseModel):
    product_name: str
    category: str | None
    total_qty: float
    shop_count: int
    avg_unit_cost: float | None
    supplier_ids: list[int]


class RecommendationOut(BaseModel):
    id: int
    product_id: int | None
    product_name: str
    suggested_supplier_id: int | None
    suggested_supplier_name: str | None
    suggested_quantity: float
    estimated_unit_cost: float | None
    confidence: float
    reasoning: str
    nearby_signal_count: int
    status: str
    created_at: datetime


class GenerateRecommendationsRequest(BaseModel):
    """Manuel tetikleme — agent'ı şimdi çalıştır."""

    since_days: int = 30
    min_signal_count: int = 2
    max_recommendations: int = 10
