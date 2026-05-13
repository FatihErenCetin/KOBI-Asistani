"""Marketplace CRUD — satınalma siparişleri, komşu shop verisi, öneriler."""

from datetime import datetime, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    MarketplaceRecommendation,
    NearbyShop,
    NearbyShopPurchase,
    Product,
    ProductSupplier,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    StockMovement,
    StockMovementReason,
    Supplier,
)

# ---------- Suppliers (marketplace view) ----------


async def list_marketplace_suppliers(
    db: AsyncSession,
    *,
    category: str | None = None,
    carrier: str | None = None,
    city: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[Supplier]:
    """Active tedarikçileri kategori/kargo/şehir/ad filtresiyle döner."""
    stmt = select(Supplier).where(Supplier.is_active.is_(True))
    if category:
        stmt = stmt.where(Supplier.category == category)
    if carrier:
        stmt = stmt.where(Supplier.carrier == carrier)
    if city:
        stmt = stmt.where(Supplier.city == city)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Supplier.name.ilike(pattern))
    stmt = stmt.order_by(Supplier.name.asc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars())


async def list_recent_suppliers(
    db: AsyncSession, *, limit: int = 6
) -> list[tuple[Supplier, datetime | None]]:
    """En son alışveriş yapılan tedarikçiler (ProductSupplier.last_purchase_at).

    PurchaseOrder son tarihleri ile birleştirilebilir ama hackathon scope'unda
    mevcut ProductSupplier alanı zaten son alımı tutuyor.
    """
    res = await db.execute(
        select(
            Supplier,
            func.max(ProductSupplier.last_purchase_at).label("last_used"),
        )
        .join(ProductSupplier, ProductSupplier.supplier_id == Supplier.id)
        .where(Supplier.is_active.is_(True))
        .where(ProductSupplier.last_purchase_at.is_not(None))
        .group_by(Supplier.id)
        .order_by(desc("last_used"))
        .limit(limit)
    )
    return [(row.Supplier, row.last_used) for row in res.all()]


# ---------- Purchase Orders ----------


async def create_purchase_order(
    db: AsyncSession,
    *,
    supplier_id: int,
    items: list[tuple[int, float, float]],  # (product_id, qty, unit_cost)
    expected_delivery=None,
    notes: str | None = None,
    admin_id: int | None = None,
    ai_suggested: bool = False,
    suggestion_reason: str | None = None,
) -> PurchaseOrder:
    total = sum(qty * cost for _, qty, cost in items)
    po = PurchaseOrder(
        supplier_id=supplier_id,
        status=PurchaseOrderStatus.DRAFT,
        total_cost=round(total, 2),
        expected_delivery=expected_delivery,
        notes=notes,
        created_by_admin_id=admin_id,
        ai_suggested=ai_suggested,
        suggestion_reason=suggestion_reason,
    )
    db.add(po)
    await db.flush()
    for product_id, qty, unit_cost in items:
        db.add(
            PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=product_id,
                quantity=qty,
                unit_cost=unit_cost,
            )
        )
    await db.flush()
    return po


async def list_purchase_orders(
    db: AsyncSession,
    *,
    status: PurchaseOrderStatus | None = None,
    supplier_id: int | None = None,
    limit: int = 50,
) -> list[PurchaseOrder]:
    stmt = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
        )
        .order_by(desc(PurchaseOrder.created_at))
        .limit(limit)
    )
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    if supplier_id:
        stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)
    res = await db.execute(stmt)
    return list(res.scalars())


async def get_purchase_order(
    db: AsyncSession, po_id: int
) -> PurchaseOrder | None:
    res = await db.execute(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.product),
        )
    )
    return res.scalar_one_or_none()


async def update_purchase_order_status(
    db: AsyncSession,
    po: PurchaseOrder,
    new_status: PurchaseOrderStatus,
    *,
    default_warehouse_id: int = 1,
) -> PurchaseOrder:
    """Status geçişi. RECEIVED'a geçince her item için StockMovement.PURCHASE yazar.

    Item.product.stock cache'i de güncellenir (lazy sync).
    """
    if po.status == new_status:
        return po
    if new_status == PurchaseOrderStatus.RECEIVED and po.status != PurchaseOrderStatus.RECEIVED:
        for item in po.items:
            product = item.product
            if product is None:
                continue
            # Cache + audit hareketi (stock_movements_crud.record otomatik bakiye günceller)
            from app.db.crud import stock_movements as sm_crud

            await sm_crud.record(
                db,
                product=product,
                delta=item.quantity,
                reason=StockMovementReason.PURCHASE,
                warehouse_id=default_warehouse_id,
                reference_type="purchase_order",
                reference_id=po.id,
                note=f"PO #{po.id} alındı",
            )
            # Ek olarak ProductSupplier.last_purchase_at güncelle (recents için)
            link_res = await db.execute(
                select(ProductSupplier).where(
                    ProductSupplier.product_id == product.id,
                    ProductSupplier.supplier_id == po.supplier_id,
                )
            )
            link = link_res.scalar_one_or_none()
            if link:
                link.last_purchase_at = datetime.utcnow()
                link.last_unit_cost = item.unit_cost
        po.received_at = datetime.utcnow()
    po.status = new_status
    await db.flush()
    return po


# ---------- Nearby shops + purchases ----------


async def list_nearby_shops(
    db: AsyncSession, *, city: str | None = None, carrier: str | None = None
) -> list[NearbyShop]:
    stmt = select(NearbyShop).where(NearbyShop.is_active.is_(True))
    if city:
        stmt = stmt.where(NearbyShop.city == city)
    if carrier:
        stmt = stmt.where(NearbyShop.preferred_carrier == carrier)
    stmt = stmt.order_by(NearbyShop.distance_km.asc().nulls_last())
    res = await db.execute(stmt)
    return list(res.scalars())


async def nearby_purchase_signals(
    db: AsyncSession,
    *,
    city: str,
    carrier: str | None = None,
    since_days: int = 30,
    min_signal_count: int = 2,
) -> list[dict]:
    """Aynı şehir + (opsiyonel) aynı kargo kullanan komşulardaki son N günlük
    satınalmaları ürün adına göre grupla, popüler olanları döner.

    Geri dönüş: [{product_name, category, total_qty, shop_count, avg_unit_cost,
                  suppliers: [id...]}]
    """
    since = datetime.utcnow() - timedelta(days=since_days)
    stmt = (
        select(
            NearbyShopPurchase.product_name,
            NearbyShopPurchase.product_category,
            func.sum(NearbyShopPurchase.quantity).label("total_qty"),
            func.count(func.distinct(NearbyShopPurchase.shop_id)).label("shop_count"),
            func.avg(NearbyShopPurchase.unit_cost).label("avg_cost"),
            func.array_agg(func.distinct(NearbyShopPurchase.supplier_id)).label("suppliers"),
        )
        .join(NearbyShop, NearbyShop.id == NearbyShopPurchase.shop_id)
        .where(NearbyShop.city == city)
        .where(NearbyShopPurchase.purchased_at >= since)
        .group_by(NearbyShopPurchase.product_name, NearbyShopPurchase.product_category)
        .having(func.count(func.distinct(NearbyShopPurchase.shop_id)) >= min_signal_count)
        .order_by(desc("shop_count"), desc("total_qty"))
    )
    if carrier:
        stmt = stmt.where(NearbyShop.preferred_carrier == carrier)
    res = await db.execute(stmt)
    rows = []
    for r in res.all():
        suppliers = [s for s in (r.suppliers or []) if s is not None]
        rows.append(
            {
                "product_name": r.product_name,
                "category": r.product_category,
                "total_qty": float(r.total_qty or 0),
                "shop_count": int(r.shop_count or 0),
                "avg_unit_cost": float(r.avg_cost) if r.avg_cost else None,
                "supplier_ids": suppliers,
            }
        )
    return rows


# ---------- Recommendations ----------


async def list_active_recommendations(
    db: AsyncSession, *, limit: int = 20
) -> list[MarketplaceRecommendation]:
    res = await db.execute(
        select(MarketplaceRecommendation)
        .where(MarketplaceRecommendation.status == "active")
        .options(
            selectinload(MarketplaceRecommendation.suggested_supplier),
            selectinload(MarketplaceRecommendation.product),
        )
        .order_by(
            desc(MarketplaceRecommendation.confidence),
            desc(MarketplaceRecommendation.created_at),
        )
        .limit(limit)
    )
    return list(res.scalars())


async def create_recommendation(
    db: AsyncSession,
    *,
    product_name: str,
    product_id: int | None = None,
    suggested_supplier_id: int | None = None,
    suggested_quantity: float,
    estimated_unit_cost: float | None,
    confidence: float,
    reasoning: str,
    nearby_signal_count: int,
) -> MarketplaceRecommendation:
    rec = MarketplaceRecommendation(
        product_name=product_name,
        product_id=product_id,
        suggested_supplier_id=suggested_supplier_id,
        suggested_quantity=suggested_quantity,
        estimated_unit_cost=estimated_unit_cost,
        confidence=confidence,
        reasoning=reasoning,
        nearby_signal_count=nearby_signal_count,
    )
    db.add(rec)
    await db.flush()
    return rec


async def dismiss_recommendation(
    db: AsyncSession, rec: MarketplaceRecommendation
) -> None:
    rec.status = "dismissed"
    await db.flush()


async def apply_recommendation(
    db: AsyncSession,
    rec: MarketplaceRecommendation,
    purchase_order_id: int,
) -> None:
    rec.status = "applied"
    rec.applied_purchase_order_id = purchase_order_id
    await db.flush()


async def get_recommendation(
    db: AsyncSession, rec_id: int
) -> MarketplaceRecommendation | None:
    res = await db.execute(
        select(MarketplaceRecommendation)
        .where(MarketplaceRecommendation.id == rec_id)
        .options(
            selectinload(MarketplaceRecommendation.suggested_supplier),
            selectinload(MarketplaceRecommendation.product),
        )
    )
    return res.scalar_one_or_none()


# Kullanılmayan import temizliği için (Product import test)
__all__ = [
    "list_marketplace_suppliers",
    "list_recent_suppliers",
    "create_purchase_order",
    "list_purchase_orders",
    "get_purchase_order",
    "update_purchase_order_status",
    "list_nearby_shops",
    "nearby_purchase_signals",
    "list_active_recommendations",
    "create_recommendation",
    "dismiss_recommendation",
    "apply_recommendation",
    "get_recommendation",
    "Product",
    "StockMovement",
]
