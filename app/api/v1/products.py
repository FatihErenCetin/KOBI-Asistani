import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_optional, get_db, require_admin
from app.db.crud import price_history as ph_crud
from app.db.crud import product_analytics as analytics
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import stock_balances as sb_crud
from app.db.crud import stock_lots as lots_crud
from app.db.crud import stock_movements as sm_crud
from app.db.crud import suppliers as suppliers_crud
from app.db.models import AdminUser, StockMovementReason
from app.schemas.bulk import BulkPriceUpdate, CsvImportResult
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
from app.schemas.lot import ExpiringLotRow, StockLotCreate, StockLotOut
from app.schemas.warehouse import WarehouseStockRow

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
        suppliers=[_link_to_out(link) for link in links],
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


@router.get("/sparklines", response_model=dict[int, list[SparklinePoint]])
async def bulk_sparklines(
    ids: str = Query(..., description="Virgülle ayrılmış ürün id'leri"),
    days: int = Query(default=7, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """Toplu sparkline — liste sayfasinda 30 paralel istek yerine 1 cagri."""
    try:
        product_ids = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    if len(product_ids) > 200:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Too many ids (max 200)")
    return await analytics.bulk_sparklines(db, product_ids, days=days)


@router.get("/export.csv")
async def export_products_csv(db: AsyncSession = Depends(get_db)):
    """Aktif urunlerin CSV cikti."""
    rows = await products_crud.list_all(db, include_inactive=False)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "id",
            "name",
            "unit",
            "price",
            "cost",
            "stock",
            "low_stock_threshold",
            "barcode",
            "category",
            "aliases",
            "description",
        ]
    )
    for p in rows:
        writer.writerow(
            [
                p.id,
                p.name,
                p.unit,
                p.price,
                p.cost,
                p.stock,
                p.low_stock_threshold,
                p.barcode or "",
                p.category or "",
                p.aliases or "",
                p.description or "",
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"},
    )


@router.post("/import.csv", response_model=CsvImportResult)
async def import_products_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    """CSV ile toplu urun import.

    Mevcut urun (id eslemesi veya kesin ad eslemesi) UPDATE, yoksa CREATE edilir.
    Beklenen kolonlar: name, unit, price, cost, stock, low_stock_threshold, barcode,
    category, aliases, description (sirasiz kabul edilir, header gerekli).
    """
    admin_id = current_admin.id if current_admin else None
    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    created = 0
    updated = 0
    skipped: list[dict] = []
    for i, row in enumerate(reader, start=2):
        try:
            name = (row.get("name") or "").strip()
            if not name:
                skipped.append({"row": i, "reason": "name boş"})
                continue
            existing = None
            if row.get("id"):
                try:
                    existing = await products_crud.get_by_id(db, int(row["id"]))
                except (ValueError, TypeError):
                    existing = None
            if existing is None:
                matches = await products_crud.search_by_name(db, name, limit=5)
                existing = next(
                    (m for m in matches if m.name.lower() == name.lower()), None
                )

            def _f(key: str, default: float = 0.0) -> float:
                val = row.get(key)
                if val in (None, ""):
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            payload = {
                "name": name,
                "unit": row.get("unit") or "kg",
                "price": _f("price"),
                "cost": _f("cost"),
                "low_stock_threshold": _f("low_stock_threshold"),
                "aliases": (row.get("aliases") or "").strip() or None,
                "description": (row.get("description") or "").strip() or None,
                "barcode": (row.get("barcode") or "").strip() or None,
                "category": (row.get("category") or "").strip() or None,
            }
            if existing:
                await products_crud.update(
                    db, existing, **payload, admin_id=admin_id, reason="CSV import"
                )
                updated += 1
            else:
                payload["stock"] = _f("stock")
                await products_crud.create(db, **payload, admin_id=admin_id)
                created += 1
        except Exception as e:
            skipped.append({"row": i, "reason": str(e)})
    await db.commit()
    return CsvImportResult(
        total_rows=created + updated + len(skipped),
        created=created,
        updated=updated,
        skipped=skipped,
    )


@router.get("/expiring", response_model=list[ExpiringLotRow])
async def expiring_lots(
    within_days: int = Query(default=14, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Onumuzdeki N gun icinde son kullanmasi gelecek lot'lar."""
    from datetime import date as _date

    rows = await lots_crud.expiring_soon(db, within_days=within_days)
    today = _date.today()
    return [
        ExpiringLotRow(
            lot_id=lot.id,
            product_id=lot.product.id,
            product_name=lot.product.name,
            lot_number=lot.lot_number,
            expiry_date=lot.expiry_date,
            days_left=(lot.expiry_date - today).days,
            quantity=lot.quantity,
        )
        for lot in rows
    ]


@router.post("/bulk-price", response_model=dict)
async def bulk_price(
    payload: BulkPriceUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    """Filtreli urunlere toplu fiyat/maliyet guncelleme. Reason zorunlu."""
    admin_id = current_admin.id if current_admin else None
    try:
        n = await products_crud.bulk_update_price(
            db,
            product_ids=payload.product_ids,
            category=payload.category,
            name_pattern=payload.name_pattern,
            operation=payload.operation,
            value=payload.value,
            target=payload.target,
            reason=payload.reason,
            admin_id=admin_id,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    await db.commit()
    return {"updated": n}


@router.post("", response_model=ProductOutDetailed, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    admin_id = current_admin.id if current_admin else None
    product = await products_crud.create(db, **payload.model_dump(), admin_id=admin_id)
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
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    admin_id = current_admin.id if current_admin else None
    await products_crud.update(
        db, p, **payload.model_dump(exclude_unset=True), admin_id=admin_id
    )
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
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    admin_id = current_admin.id if current_admin else None
    await products_crud.set_stock(db, p, payload.stock, admin_id=admin_id)
    await db.commit()
    return _to_out(p)


@router.post("/{product_id}/stock-movements", response_model=ProductOut)
async def adjust_stock(
    product_id: int,
    payload: StockAdjust,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    try:
        reason = StockMovementReason(payload.reason)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    admin_id = current_admin.id if current_admin else None
    await products_crud.adjust_stock(
        db,
        p,
        payload.delta,
        reason=reason,
        warehouse_id=payload.warehouse_id,
        note=payload.note,
        admin_id=admin_id,
    )
    await db.commit()
    return _to_out(p)


@router.get("/{product_id}/price-history", response_model=list[PriceHistoryRow])
async def get_price_history(product_id: int, db: AsyncSession = Depends(get_db)):
    rows = await ph_crud.list_for_product_with_admin(db, product_id)
    return [
        PriceHistoryRow(
            id=r.id,
            field=r.field.value,
            old_value=r.old_value,
            new_value=r.new_value,
            reason=r.reason,
            changed_at=r.changed_at,
            changed_by_admin_id=r.changed_by_admin_id,
            changed_by_admin_name=admin_name,
        )
        for r, admin_name in rows
    ]


@router.get("/{product_id}/movements", response_model=list[StockMovementRow])
async def get_movements(product_id: int, db: AsyncSession = Depends(get_db)):
    rows = await sm_crud.list_for_product_with_admin(db, product_id)
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
            created_by_admin_name=admin_name,
        )
        for r, admin_name in rows
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


@router.get("/{product_id}/lots", response_model=list[StockLotOut])
async def list_product_lots(
    product_id: int,
    warehouse_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Bir urunun lot'larini listele (sadece quantity > 0 olanlar)."""
    lots = await lots_crud.list_for_product(
        db, product_id, warehouse_id=warehouse_id, only_with_stock=True
    )
    return [
        StockLotOut(
            id=lot.id,
            product_id=lot.product_id,
            warehouse_id=lot.warehouse_id,
            warehouse_name=lot.warehouse.name if lot.warehouse else None,
            lot_number=lot.lot_number,
            quantity=lot.quantity,
            expiry_date=lot.expiry_date,
            supplier_id=lot.supplier_id,
            supplier_name=lot.supplier.name if lot.supplier else None,
            received_at=lot.received_at,
            note=lot.note,
        )
        for lot in lots
    ]


@router.post(
    "/{product_id}/lots", response_model=StockLotOut, status_code=status.HTTP_201_CREATED
)
async def create_product_lot(
    product_id: int,
    payload: StockLotCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    """Yeni lot ekle + StockMovement(PURCHASE) yazsin ki cache senkron kalsin."""
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    admin_id = current_admin.id if current_admin else None
    lot = await lots_crud.create(
        db,
        product_id=product_id,
        warehouse_id=payload.warehouse_id,
        lot_number=payload.lot_number,
        quantity=payload.quantity,
        expiry_date=payload.expiry_date,
        supplier_id=payload.supplier_id,
        note=payload.note,
    )
    # Movement de yaz — balance + cache otomatik senkron olur
    await products_crud.adjust_stock(
        db,
        p,
        payload.quantity,
        reason=StockMovementReason.PURCHASE,
        warehouse_id=payload.warehouse_id,
        note=f"Lot {payload.lot_number} ekleme",
        admin_id=admin_id,
    )
    await db.commit()
    return StockLotOut(
        id=lot.id,
        product_id=lot.product_id,
        warehouse_id=lot.warehouse_id,
        warehouse_name=None,
        lot_number=lot.lot_number,
        quantity=lot.quantity,
        expiry_date=lot.expiry_date,
        supplier_id=lot.supplier_id,
        supplier_name=None,
        received_at=lot.received_at,
        note=lot.note,
    )


@router.get("/{product_id}/warehouses", response_model=list[WarehouseStockRow])
async def product_warehouse_breakdown(
    product_id: int, db: AsyncSession = Depends(get_db)
):
    """Bir urunun deop bazinda stok dagilimi."""
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    rows = await sb_crud.breakdown_for_product(db, product_id)
    return [
        WarehouseStockRow(
            warehouse_id=r.warehouse_id,
            warehouse_name=r.warehouse.name if r.warehouse else "?",
            quantity=r.quantity,
        )
        for r in rows
    ]


@router.get("/{product_id}/suppliers", response_model=list[ProductSupplierLinkOut])
async def list_links(product_id: int, db: AsyncSession = Depends(get_db)):
    links = await ps_crud.list_for_product(db, product_id)
    return [_link_to_out(link) for link in links]


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
