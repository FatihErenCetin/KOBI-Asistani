from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import price_history as price_history_crud
from app.db.crud import stock_movements as stock_movements_crud
from app.db.models import PriceHistoryField, Product, StockMovementReason


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)


async def search_by_name(db: AsyncSession, query: str, limit: int = 10) -> list[Product]:
    """Ad ve alias'larda case-insensitive arama. Sadece aktif urunler."""
    pattern = f"%{query.lower()}%"
    res = await db.execute(
        select(Product)
        .where(
            Product.is_active.is_(True),
            or_(Product.name.ilike(pattern), Product.aliases.ilike(pattern)),
        )
        .limit(limit)
    )
    return list(res.scalars())


async def list_all(
    db: AsyncSession,
    low_stock_only: bool = False,
    search: str | None = None,
    include_inactive: bool = False,
) -> list[Product]:
    stmt = select(Product)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if low_stock_only:
        stmt = stmt.where(Product.stock <= Product.low_stock_threshold)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Product.name.ilike(pattern),
                Product.aliases.ilike(pattern),
                Product.barcode.ilike(pattern),
            )
        )
    res = await db.execute(stmt.order_by(Product.name))
    return list(res.scalars())


async def adjust_stock(
    db: AsyncSession,
    product: Product,
    delta: float,
    *,
    reason: StockMovementReason,
    warehouse_id: int | None = None,
    note: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    admin_id: int | None = None,
) -> Product:
    """Stoga delta uygular ve audit kaydi yazar. Tek atomik nokta.

    warehouse_id verilmezse default depo kullanilir.
    """
    await stock_movements_crud.record(
        db,
        product=product,
        delta=delta,
        reason=reason,
        warehouse_id=warehouse_id,
        note=note,
        reference_type=reference_type,
        reference_id=reference_id,
        admin_id=admin_id,
    )
    return product


async def set_stock(
    db: AsyncSession,
    product: Product,
    new_stock: float,
    *,
    warehouse_id: int | None = None,
    note: str | None = None,
    admin_id: int | None = None,
) -> Product:
    """Mutlak stok ayari — delta hesaplar, audit'ten gecirir. warehouse seçimi opsiyonel."""
    delta = new_stock - product.stock
    if delta == 0:
        return product
    return await adjust_stock(
        db,
        product,
        delta,
        reason=StockMovementReason.ADJUSTMENT,
        warehouse_id=warehouse_id,
        note=note or "Manuel sayim/duzeltme",
        admin_id=admin_id,
    )


async def create(
    db: AsyncSession,
    *,
    name: str,
    unit: str,
    price: float,
    cost: float = 0.0,
    stock: float = 0.0,
    low_stock_threshold: float = 0.0,
    max_stock: float | None = None,
    aliases: str | None = None,
    description: str | None = None,
    barcode: str | None = None,
    category: str | None = None,
    admin_id: int | None = None,
) -> Product:
    product = Product(
        name=name,
        unit=unit,
        price=price,
        cost=cost,
        stock=0,
        low_stock_threshold=low_stock_threshold,
        max_stock=max_stock,
        aliases=aliases,
        description=description,
        barcode=barcode,
        category=category,
        is_active=True,
    )
    db.add(product)
    await db.flush()

    await price_history_crud.record(
        db,
        product_id=product.id,
        field=PriceHistoryField.PRICE,
        old_value=None,
        new_value=price,
        reason="Ilk olusturma",
        admin_id=admin_id,
    )
    if cost > 0:
        await price_history_crud.record(
            db,
            product_id=product.id,
            field=PriceHistoryField.COST,
            old_value=None,
            new_value=cost,
            reason="Ilk olusturma",
            admin_id=admin_id,
        )

    if stock > 0:
        await adjust_stock(
            db,
            product,
            stock,
            reason=StockMovementReason.INITIAL,
            note="Acilis stogu",
            admin_id=admin_id,
        )

    return product


async def update(
    db: AsyncSession,
    product: Product,
    *,
    name: str | None = None,
    unit: str | None = None,
    price: float | None = None,
    cost: float | None = None,
    low_stock_threshold: float | None = None,
    max_stock: float | None = None,
    aliases: str | None = None,
    description: str | None = None,
    barcode: str | None = None,
    category: str | None = None,
    reason: str | None = None,
    admin_id: int | None = None,
) -> Product:
    if name is not None:
        product.name = name
    if unit is not None:
        product.unit = unit
    if low_stock_threshold is not None:
        product.low_stock_threshold = low_stock_threshold
    if max_stock is not None:
        product.max_stock = max_stock
    if aliases is not None:
        product.aliases = aliases
    if description is not None:
        product.description = description
    if barcode is not None:
        product.barcode = barcode
    if category is not None:
        product.category = category

    if price is not None and price != product.price:
        await price_history_crud.record(
            db,
            product_id=product.id,
            field=PriceHistoryField.PRICE,
            old_value=product.price,
            new_value=price,
            reason=reason,
            admin_id=admin_id,
        )
        product.price = price

    if cost is not None and cost != product.cost:
        await price_history_crud.record(
            db,
            product_id=product.id,
            field=PriceHistoryField.COST,
            old_value=product.cost,
            new_value=cost,
            reason=reason,
            admin_id=admin_id,
        )
        product.cost = cost

    await db.flush()
    return product


async def soft_delete(db: AsyncSession, product: Product) -> Product:
    product.is_active = False
    await db.flush()
    return product


async def bulk_update_price(
    db: AsyncSession,
    *,
    product_ids: list[int] | None,
    category: str | None,
    name_pattern: str | None,
    operation: str,
    value: float,
    target: str,
    reason: str,
    admin_id: int | None,
) -> int:
    """Filtreli urunlere toplu fiyat/maliyet guncelleme. Her degisim history yazar.

    operation: percent_increase | percent_decrease | set_absolute
    target: price | cost
    """
    if target not in ("price", "cost"):
        raise ValueError("target must be 'price' or 'cost'")
    if operation not in ("percent_increase", "percent_decrease", "set_absolute"):
        raise ValueError("invalid operation")

    stmt = select(Product).where(Product.is_active.is_(True))
    if product_ids:
        stmt = stmt.where(Product.id.in_(product_ids))
    if category:
        stmt = stmt.where(Product.category == category)
    if name_pattern:
        stmt = stmt.where(Product.name.ilike(f"%{name_pattern}%"))
    products = list((await db.execute(stmt)).scalars())

    for p in products:
        current = p.price if target == "price" else p.cost
        if operation == "percent_increase":
            new_val = round(current * (1 + value / 100), 2)
        elif operation == "percent_decrease":
            new_val = round(current * (1 - value / 100), 2)
        else:
            new_val = round(value, 2)
        kwargs = {target: new_val, "reason": reason, "admin_id": admin_id}
        await update(db, p, **kwargs)
    return len(products)
