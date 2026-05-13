"""Prod-safe demo verisi zenginleştirici.

Mevcut veriyi silmez. Sadece eksikleri doldurur:
- Yoksa ek depolar (Şube, Soğuk Hava, Araç) ekler.
- Hiç lot yoksa LOT_CATALOG'u uygular (mevcut ürünlerin var olan stokları
  üzerinden).
- Mevcut ürünler hep Ana Depo'daysa, MULTI_WAREHOUSE_SPLIT'te tanımlı ürünleri
  hedef depolara dağıtır (transfer movement'leri yazar).

Idempotent: birden çok kez çalıştırılabilir; eklenen şey yoksa nothing happens.
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import stock_balances as sb_crud
from app.db.models import (
    Product,
    StockBalance,
    StockLot,
    StockMovement,
    StockMovementReason,
    Warehouse,
)
from app.db.seed import LOT_CATALOG, MULTI_WAREHOUSE_SPLIT, WAREHOUSE_CATALOG

logger = logging.getLogger(__name__)


async def ensure_warehouses(db: AsyncSession) -> dict:
    """WAREHOUSE_CATALOG'taki tüm depoların var olduğunu garanti et. Idempotent."""
    res = await db.execute(select(Warehouse))
    existing_codes = {w.code: w for w in res.scalars()}
    created = 0
    for name, code, address, is_default in WAREHOUSE_CATALOG:
        if code in existing_codes:
            continue
        # is_default=True olan başka biri varsa, yeni eklenen default=False
        if is_default and any(
            w.is_default for w in existing_codes.values()
        ):
            is_default = False
        db.add(
            Warehouse(
                name=name,
                code=code,
                address=address,
                is_default=is_default,
                is_active=True,
            )
        )
        created += 1
    await db.flush()
    return {"warehouses_created": created}


async def ensure_lots(db: AsyncSession) -> dict:
    """LOT_CATALOG'u idempotent uygula. lot_number zaten varsa eklemez.

    Lot eklerken ayrıca StockMovement yazmaz — mevcut Product.stock cache
    dokunulmuyor. Lot, mevcut StockBalance içinden 'görünür' olarak temsili.
    """
    res = await db.execute(select(Product).where(Product.is_active.is_(True)))
    products_by_name = {p.name: p for p in res.scalars()}

    wh_res = await db.execute(select(Warehouse))
    code_to_id = {w.code: w.id for w in wh_res.scalars()}
    default_id = next(
        (w.id for w in (await db.execute(select(Warehouse))).scalars() if w.is_default),
        None,
    )

    splits_by_name = {name: split for name, split in MULTI_WAREHOUSE_SPLIT}
    existing_lots_res = await db.execute(select(StockLot.lot_number))
    existing_lot_nos = {r[0] for r in existing_lots_res.all()}

    created = 0
    for product_name, lot_no, ratio, skt_offset, _sup_idx in LOT_CATALOG:
        if lot_no in existing_lot_nos:
            continue
        p = products_by_name.get(product_name)
        if p is None:
            continue
        split = splits_by_name.get(product_name, [("main", 1.0)])
        primary_code = max(split, key=lambda s: s[1])[0]
        wh_id = code_to_id.get(primary_code, default_id)
        if wh_id is None:
            continue
        # Lot quantity = ürünün hedef depodaki balance'ının ratio'su
        bal_res = await db.execute(
            select(StockBalance.quantity).where(
                StockBalance.product_id == p.id,
                StockBalance.warehouse_id == wh_id,
            )
        )
        bal_qty = float(bal_res.scalar_one_or_none() or 0)
        if bal_qty <= 0:
            # Hedef depoda hiç stok yok, lot eklemenin anlamı yok
            continue
        lot_qty = round(bal_qty * ratio, 2)
        if lot_qty <= 0:
            continue
        expiry = date.today() + timedelta(days=skt_offset)
        db.add(
            StockLot(
                product_id=p.id,
                warehouse_id=wh_id,
                lot_number=lot_no,
                quantity=lot_qty,
                expiry_date=expiry,
                received_at=datetime.utcnow() - timedelta(days=2),
                note="Enrich script tarafından eklendi",
            )
        )
        created += 1
    await db.flush()
    return {"lots_created": created}


async def ensure_multi_warehouse(db: AsyncSession) -> dict:
    """MULTI_WAREHOUSE_SPLIT'teki ürünleri hedef depolara TRANSFER hareketi olmadan
    sadece balance bazında dağıt. Mevcut ürünün toplam stoğunu korur.

    Sadece bir ürünün tek (default) depoda balance'ı varsa çalışır;
    zaten birden çok depodaysa atlanır.
    """
    wh_res = await db.execute(select(Warehouse))
    warehouses = list(wh_res.scalars())
    code_to_id = {w.code: w.id for w in warehouses}
    default_id = next((w.id for w in warehouses if w.is_default), None)
    if default_id is None or len(warehouses) < 2:
        return {"products_split": 0}

    splits_by_name = {name: split for name, split in MULTI_WAREHOUSE_SPLIT}
    res = await db.execute(select(Product).where(Product.is_active.is_(True)))
    products = list(res.scalars())

    moved = 0
    for p in products:
        split = splits_by_name.get(p.name)
        if not split:
            continue
        # Kaç ayrı warehouse'ta balance'ı var?
        bals_res = await db.execute(
            select(StockBalance).where(StockBalance.product_id == p.id)
        )
        bals = list(bals_res.scalars())
        if len(bals) >= 2:
            continue  # zaten dağıtılmış, dokunma
        if len(bals) == 0:
            continue  # hiç stok yok
        main_bal = bals[0]
        if main_bal.warehouse_id != default_id:
            continue  # default depoda değil, anlamlı transfer mümkün değil
        total = main_bal.quantity
        if total <= 0:
            continue
        # Dağılımı uygula
        main_bal.quantity = 0
        for code, ratio in split:
            wh_id = code_to_id.get(code, default_id)
            qty = round(total * ratio, 2)
            if qty <= 0:
                continue
            bal = await sb_crud.get_or_create(db, p.id, wh_id)
            bal.quantity += qty
            # Audit: transfer hareketi (delta=0 değişimini açıklamak için 2 movement)
            db.add(
                StockMovement(
                    product_id=p.id,
                    warehouse_id=wh_id,
                    delta=qty,
                    reason=StockMovementReason.ADJUSTMENT,
                    balance_after=bal.quantity,
                    note=f"Depo dağılımı: Ana Depo → {code}",
                )
            )
        # Product.stock cache aynı kalıyor (toplam korundu)
        moved += 1
    await db.flush()
    return {"products_split": moved}


async def enrich_all(db: AsyncSession) -> dict:
    """Tüm idempotent zenginleştirmeleri sırayla uygula."""
    result = {}
    result.update(await ensure_warehouses(db))
    result.update(await ensure_multi_warehouse(db))
    # Lot ekleme balance'lara bağlı, multi-warehouse'tan sonra çalışmalı
    result.update(await ensure_lots(db))
    await db.commit()
    logger.info("Demo enrichment complete: %s", result)
    return result
