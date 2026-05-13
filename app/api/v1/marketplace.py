"""Marketplace API'leri — tedarikçi pazarı, satınalma siparişi, AI önerileri."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_optional, get_db, require_admin
from app.db.crud import marketplace as mp_crud
from app.db.models import (
    AdminUser,
    NearbyShop,
    ProductSupplier,
    PurchaseOrder,
    PurchaseOrderStatus,
    Supplier,
)
from app.schemas.marketplace import (
    GenerateRecommendationsRequest,
    NearbyShopOut,
    NearbySignalOut,
    PurchaseOrderCreate,
    PurchaseOrderOut,
    PurchaseOrderStatusUpdate,
    RecentSupplierOut,
    RecommendationOut,
    SupplierMarketplaceOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/marketplace",
    tags=["marketplace"],
    dependencies=[Depends(require_admin)],
)


# ---------- Helpers ----------


def _supplier_to_out(s: Supplier, last_used: datetime | None = None, links: int = 0) -> SupplierMarketplaceOut:
    return SupplierMarketplaceOut(
        id=s.id,
        name=s.name,
        category=s.category,
        carrier=s.carrier,
        city=s.city,
        district=s.district,
        description=s.description,
        rating=s.rating,
        contact_name=s.contact_name,
        phone=s.phone,
        email=s.email,
        last_used_at=last_used,
        linked_product_count=links,
    )


def _po_to_out(po: PurchaseOrder) -> PurchaseOrderOut:
    from app.schemas.marketplace import PurchaseOrderItemOut

    return PurchaseOrderOut(
        id=po.id,
        supplier_id=po.supplier_id,
        supplier_name=po.supplier.name if po.supplier else "?",
        status=po.status.value,
        total_cost=po.total_cost,
        expected_delivery=po.expected_delivery,
        received_at=po.received_at,
        notes=po.notes,
        ai_suggested=po.ai_suggested,
        suggestion_reason=po.suggestion_reason,
        items=[
            PurchaseOrderItemOut(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product.name if it.product else "?",
                product_unit=it.product.unit if it.product else "",
                quantity=it.quantity,
                unit_cost=it.unit_cost,
                line_total=round(it.quantity * it.unit_cost, 2),
            )
            for it in (po.items or [])
        ],
        created_at=po.created_at,
    )


def _parse_status(value: str) -> PurchaseOrderStatus:
    try:
        return PurchaseOrderStatus(value.lower())
    except ValueError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bilinmeyen status: {value}. Desteklenen: "
            + ", ".join(s.value for s in PurchaseOrderStatus),
        ) from e


async def _count_supplier_links(db: AsyncSession, supplier_id: int) -> int:
    res = await db.execute(
        select(func.count(ProductSupplier.id)).where(
            ProductSupplier.supplier_id == supplier_id
        )
    )
    return int(res.scalar_one() or 0)


# ---------- Suppliers ----------


@router.get("/suppliers", response_model=list[SupplierMarketplaceOut])
async def list_suppliers(
    category: str | None = Query(default=None),
    carrier: str | None = Query(default=None),
    city: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Marketplace tedarikçileri (filtreli)."""
    rows = await mp_crud.list_marketplace_suppliers(
        db, category=category, carrier=carrier, city=city, search=search
    )
    out: list[SupplierMarketplaceOut] = []
    for s in rows:
        links = await _count_supplier_links(db, s.id)
        out.append(_supplier_to_out(s, links=links))
    return out


@router.get("/suppliers/recent", response_model=list[RecentSupplierOut])
async def recent_suppliers(
    limit: int = Query(default=6, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Son alışveriş yapılan tedarikçiler."""
    rows = await mp_crud.list_recent_suppliers(db, limit=limit)
    out: list[RecentSupplierOut] = []
    for s, last in rows:
        if last is None:
            continue
        links = await _count_supplier_links(db, s.id)
        out.append(
            RecentSupplierOut(
                supplier=_supplier_to_out(s, last_used=last, links=links),
                last_used_at=last,
            )
        )
    return out


@router.get("/suppliers/filters")
async def supplier_filters(db: AsyncSession = Depends(get_db)):
    """UI filter chip'leri için kategori/kargo/şehir distinct değerleri."""
    cat_res = await db.execute(
        select(Supplier.category)
        .where(Supplier.is_active.is_(True))
        .where(Supplier.category.is_not(None))
        .distinct()
    )
    car_res = await db.execute(
        select(Supplier.carrier)
        .where(Supplier.is_active.is_(True))
        .where(Supplier.carrier.is_not(None))
        .distinct()
    )
    city_res = await db.execute(
        select(Supplier.city)
        .where(Supplier.is_active.is_(True))
        .where(Supplier.city.is_not(None))
        .distinct()
    )
    return {
        "categories": sorted(c for c in cat_res.scalars() if c),
        "carriers": sorted(c for c in car_res.scalars() if c),
        "cities": sorted(c for c in city_res.scalars() if c),
    }


# ---------- Purchase Orders ----------


@router.get("/purchase-orders", response_model=list[PurchaseOrderOut])
async def list_pos(
    status_filter: str | None = Query(default=None, alias="status"),
    supplier_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    status_enum = _parse_status(status_filter) if status_filter else None
    rows = await mp_crud.list_purchase_orders(
        db, status=status_enum, supplier_id=supplier_id
    )
    return [_po_to_out(p) for p in rows]


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_po(
    payload: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    supplier_res = await db.execute(
        select(Supplier).where(Supplier.id == payload.supplier_id)
    )
    supplier = supplier_res.scalar_one_or_none()
    if supplier is None or not supplier.is_active:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Tedarikçi bulunamadı veya pasif"
        )
    admin_id = current_admin.id if current_admin else None
    # AI önerisi varsa link'le
    suggestion_reason = None
    ai_suggested = False
    rec = None
    if payload.recommendation_id:
        rec = await mp_crud.get_recommendation(db, payload.recommendation_id)
        if rec is None or rec.status != "active":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Öneri bulunamadı veya artık aktif değil",
            )
        ai_suggested = True
        suggestion_reason = rec.reasoning

    po = await mp_crud.create_purchase_order(
        db,
        supplier_id=payload.supplier_id,
        items=[(i.product_id, i.quantity, i.unit_cost) for i in payload.items],
        expected_delivery=payload.expected_delivery,
        notes=payload.notes,
        admin_id=admin_id,
        ai_suggested=ai_suggested,
        suggestion_reason=suggestion_reason,
    )
    if rec is not None:
        await mp_crud.apply_recommendation(db, rec, po.id)
    await db.commit()
    refreshed = await mp_crud.get_purchase_order(db, po.id)
    return _po_to_out(refreshed)


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def get_po(po_id: int, db: AsyncSession = Depends(get_db)):
    po = await mp_crud.get_purchase_order(db, po_id)
    if po is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sipariş bulunamadı")
    return _po_to_out(po)


@router.patch("/purchase-orders/{po_id}/status", response_model=PurchaseOrderOut)
async def update_po_status(
    po_id: int,
    payload: PurchaseOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    po = await mp_crud.get_purchase_order(db, po_id)
    if po is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sipariş bulunamadı")
    new_status = _parse_status(payload.status)
    await mp_crud.update_purchase_order_status(db, po, new_status)
    await db.commit()
    refreshed = await mp_crud.get_purchase_order(db, po_id)
    return _po_to_out(refreshed)


# ---------- Nearby shops + signals ----------


@router.get("/nearby-shops", response_model=list[NearbyShopOut])
async def list_shops(
    city: str | None = Query(default=None),
    carrier: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    rows = await mp_crud.list_nearby_shops(db, city=city, carrier=carrier)
    return [
        NearbyShopOut(
            id=s.id,
            name=s.name,
            shop_type=s.shop_type,
            city=s.city,
            district=s.district,
            distance_km=s.distance_km,
            preferred_carrier=s.preferred_carrier,
        )
        for s in rows
    ]


@router.get("/nearby-signals", response_model=list[NearbySignalOut])
async def get_signals(
    city: str = Query(...),
    carrier: str | None = Query(default=None),
    since_days: int = Query(default=30, ge=1, le=180),
    min_signal_count: int = Query(default=2, ge=1),
    db: AsyncSession = Depends(get_db),
):
    rows = await mp_crud.nearby_purchase_signals(
        db,
        city=city,
        carrier=carrier,
        since_days=since_days,
        min_signal_count=min_signal_count,
    )
    return [NearbySignalOut(**r) for r in rows]


# ---------- AI Recommendations ----------


@router.get("/recommendations", response_model=list[RecommendationOut])
async def list_recommendations(db: AsyncSession = Depends(get_db)):
    rows = await mp_crud.list_active_recommendations(db)
    return [
        RecommendationOut(
            id=r.id,
            product_id=r.product_id,
            product_name=r.product_name,
            suggested_supplier_id=r.suggested_supplier_id,
            suggested_supplier_name=(
                r.suggested_supplier.name if r.suggested_supplier else None
            ),
            suggested_quantity=r.suggested_quantity,
            estimated_unit_cost=r.estimated_unit_cost,
            confidence=r.confidence,
            reasoning=r.reasoning,
            nearby_signal_count=r.nearby_signal_count,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/recommendations/generate", response_model=list[RecommendationOut])
async def generate_recommendations(
    payload: GenerateRecommendationsRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    """Manuel tetikle: AI advisor şu an çalışsın, yeni öneriler üretsin."""
    from app.services import marketplace_advisor

    admin = current_admin
    # current_admin yoksa (ADMIN_TOKEN ile çağrı), default lokasyon kullanılır
    new_recs = await marketplace_advisor.run_analysis(
        db,
        admin=admin,
        since_days=payload.since_days,
        min_signal_count=payload.min_signal_count,
        max_recommendations=payload.max_recommendations,
    )
    await db.commit()
    return [
        RecommendationOut(
            id=r.id,
            product_id=r.product_id,
            product_name=r.product_name,
            suggested_supplier_id=r.suggested_supplier_id,
            suggested_supplier_name=(
                r.suggested_supplier.name if r.suggested_supplier else None
            ),
            suggested_quantity=r.suggested_quantity,
            estimated_unit_cost=r.estimated_unit_cost,
            confidence=r.confidence,
            reasoning=r.reasoning,
            nearby_signal_count=r.nearby_signal_count,
            status=r.status,
            created_at=r.created_at,
        )
        for r in new_recs
    ]


@router.post(
    "/recommendations/{rec_id}/dismiss", status_code=status.HTTP_204_NO_CONTENT
)
async def dismiss_rec(rec_id: int, db: AsyncSession = Depends(get_db)):
    rec = await mp_crud.get_recommendation(db, rec_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Öneri bulunamadı")
    await mp_crud.dismiss_recommendation(db, rec)
    await db.commit()


# Re-export model usage for ruff
_NEARBY_REF = NearbyShop
