from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import price_history as ph_crud
from app.db.crud import product_analytics as analytics
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import stock_movements as sm_crud
from app.db.crud import suppliers as suppliers_crud
from app.db.models import StockMovementReason
from app.schemas.product import (
    ProductCreate,
    ProductOut,
    ProductOutDetailed,
    ProductUpdate,
    StockAdjust,
    StockUpdate,
)
from app.schemas.product_history import (
    PriceHistoryRow,
    ProductAnalytics,
    SparklinePoint,
    StockMovementRow,
)
from app.schemas.supplier import (
    ProductSupplierLinkIn,
    ProductSupplierLinkOut,
    ProductSupplierLinkUpdate,
)

router = APIRouter(
    prefix="/products", tags=["products"], dependencies=[Depends(require_admin)]
)


def _to_out(p) -> ProductOut:
    margin = None
    if p.cost and p.cost > 0 and p.price > 0:
        margin = round((p.price - p.cost) / p.price * 100, 1)
    return ProductOut(
        id=p.id,
        name=p.name,
        aliases=p.aliases,
        unit=p.unit,
        price=p.price,
        cost=p.cost,
        stock=p.stock,
        low_stock_threshold=p.low_stock_threshold,
        description=p.description,
        barcode=p.barcode,
        category=p.category,
        is_active=p.is_active,
        is_low=p.stock <= p.low_stock_threshold,
        profit_margin_pct=margin,
    )


def _link_to_out(link) -> ProductSupplierLinkOut:
    return ProductSupplierLinkOut(
        id=link.id,
        supplier_id=link.supplier_id,
        supplier_name=link.supplier.name if link.supplier else "?",
        supplier_sku=link.supplier_sku,
        last_unit_cost=link.last_unit_cost,
        last_purchase_at=link.last_purchase_at,
        lead_time_days=link.lead_time_days,
        is_preferred=link.is_preferred,
        notes=link.notes,
    )


async def _detailed(db: AsyncSession, product_id: int) -> ProductOutDetailed:
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    out = _to_out(p)
    links = await ps_crud.list_for_product(db, product_id)
    anal = await analytics.for_product(db, p)
    return ProductOutDetailed(
        **out.model_dump(),
        created_at=p.created_at,
        updated_at=p.updated_at,
        suppliers=[_link_to_out(l) for l in links],
        analytics=ProductAnalytics(**anal),
    )


@router.get("", response_model=list[ProductOut])
async def list_products(
    search: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    rows = await products_crud.list_all(
        db,
        low_stock_only=low_stock_only,
        search=search,
        include_inactive=include_inactive,
    )
    return [_to_out(p) for p in rows]


@router.post("", response_model=ProductOutDetailed, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = await products_crud.create(db, **payload.model_dump())
    await db.commit()
    return await _detailed(db, product.id)


@router.get("/{product_id}", response_model=ProductOutDetailed)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await _detailed(db, product_id)


@router.patch("/{product_id}", response_model=ProductOutDetailed)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    await products_crud.update(db, p, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return await _detailed(db, product_id)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    await products_crud.soft_delete(db, p)
    await db.commit()


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def update_stock_absolute(
    product_id: int,
    payload: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    await products_crud.set_stock(db, p, payload.stock)
    await db.commit()
    return _to_out(p)


@router.post("/{product_id}/stock-movements", response_model=ProductOut)
async def adjust_stock(
    product_id: int,
    payload: StockAdjust,
    db: AsyncSession = Depends(get_db),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    try:
        reason = StockMovementReason(payload.reason)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    await products_crud.adjust_stock(
        db, p, payload.delta, reason=reason, note=payload.note
    )
    await db.commit()
    return _to_out(p)


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryRow])
async def get_price_history(product_id: int, db: AsyncSession = Depends(get_db)):
    rows = await ph_crud.list_for_product(db, product_id)
    return [
        PriceHistoryRow(
            id=r.id,
            field=r.field.value,
            old_value=r.old_value,
            new_value=r.new_value,
            reason=r.reason,
            changed_at=r.changed_at,
            changed_by_admin_id=r.changed_by_admin_id,
        )
        for r in rows
    ]


@router.get("/{product_id}/movements", response_model=list[StockMovementRow])
async def get_movements(product_id: int, db: AsyncSession = Depends(get_db)):
    rows = await sm_crud.list_for_product(db, product_id)
    return [
        StockMovementRow(
            id=r.id,
            delta=r.delta,
            reason=r.reason.value,
            reference_type=r.reference_type,
            reference_id=r.reference_id,
            note=r.note,
            balance_after=r.balance_after,
            created_at=r.created_at,
            created_by_admin_id=r.created_by_admin_id,
        )
        for r in rows
    ]


@router.get("/{product_id}/analytics", response_model=ProductAnalytics)
async def get_analytics(product_id: int, db: AsyncSession = Depends(get_db)):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return await analytics.for_product(db, p)


@router.get("/{product_id}/sparkline", response_model=list[SparklinePoint])
async def get_sparkline(
    product_id: int,
    days: int = Query(default=7, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    return await analytics.daily_sales_sparkline(db, product_id, days=days)


@router.get("/{product_id}/suppliers", response_model=list[ProductSupplierLinkOut])
async def list_links(product_id: int, db: AsyncSession = Depends(get_db)):
    links = await ps_crud.list_for_product(db, product_id)
    return [_link_to_out(l) for l in links]


@router.post(
    "/{product_id}/suppliers",
    response_model=ProductSupplierLinkOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_link(
    product_id: int,
    payload: ProductSupplierLinkIn,
    db: AsyncSession = Depends(get_db),
):
    s = await suppliers_crud.get_by_id(db, payload.supplier_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    existing = await ps_crud.get_link(db, product_id, payload.supplier_id)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already linked")
    await ps_crud.add_link(db, product_id=product_id, **payload.model_dump())
    await db.commit()
    link = await ps_crud.get_link(db, product_id, payload.supplier_id)
    return _link_to_out(link)


@router.patch(
    "/{product_id}/suppliers/{supplier_id}",
    response_model=ProductSupplierLinkOut,
)
async def patch_link(
    product_id: int,
    supplier_id: int,
    payload: ProductSupplierLinkUpdate,
    db: AsyncSession = Depends(get_db),
):
    link = await ps_crud.get_link(db, product_id, supplier_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    await ps_crud.update_link(db, link, **payload.model_dump(exclude_unset=True))
    await db.commit()
    link = await ps_crud.get_link(db, product_id, supplier_id)
    return _link_to_out(link)


@router.delete(
    "/{product_id}/suppliers/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_link(
    product_id: int,
    supplier_id: int,
    db: AsyncSession = Depends(get_db),
):
    link = await ps_crud.get_link(db, product_id, supplier_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link not found")
    await ps_crud.remove_link(db, link)
    await db.commit()
