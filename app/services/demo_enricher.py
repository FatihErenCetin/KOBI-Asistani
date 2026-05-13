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
import random
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import stock_balances as sb_crud
from app.db.models import (
    AdminUser,
    Expense,
    ExpenseCategory,
    NearbyShop,
    NearbyShopPurchase,
    PriceHistory,
    PriceHistoryField,
    Product,
    ProductSupplier,
    SocialAccount,
    SocialPlatform,
    SocialPost,
    SocialPostStatus,
    StockBalance,
    StockLot,
    StockMovement,
    StockMovementReason,
    Supplier,
    Warehouse,
)
from app.db.seed import (
    LOT_CATALOG,
    MULTI_WAREHOUSE_SPLIT,
    NEARBY_PURCHASE_CATALOG,
    NEARBY_SHOP_CATALOG,
    SOCIAL_ACCOUNT_CATALOG,
    SOCIAL_POST_CATALOG,
    SUPPLIER_CATALOG,
    SUPPLIER_META,
    WAREHOUSE_CATALOG,
)

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


async def ensure_suppliers(db: AsyncSession) -> dict:
    """SUPPLIER_CATALOG'taki 5 tedarikçiyi idempotent ekle (isim eşleşmesi)."""
    res = await db.execute(select(Supplier))
    existing_names = {s.name for s in res.scalars()}

    created = 0
    for name, contact, phone, email, address in SUPPLIER_CATALOG:
        if name in existing_names:
            continue
        db.add(
            Supplier(
                name=name,
                contact_name=contact,
                phone=phone,
                email=email,
                address=address,
                is_active=True,
            )
        )
        created += 1
    await db.flush()
    return {"suppliers_created": created}


async def ensure_product_supplier_links(db: AsyncSession) -> dict:
    """Hiç tedarikçi bağı olmayan ürünlere 1-2 random tedarikçi bağla.

    Idempotent: zaten bağı varsa atlanır. Random seed sabit (deterministik).
    """
    res = await db.execute(select(Supplier).where(Supplier.is_active.is_(True)))
    suppliers = list(res.scalars())
    if not suppliers:
        return {"supplier_links_created": 0}

    products_res = await db.execute(
        select(Product).where(Product.is_active.is_(True))
    )
    products = list(products_res.scalars())

    # Hangi ürünlerin zaten linki var?
    linked_res = await db.execute(select(ProductSupplier.product_id).distinct())
    already_linked = {row[0] for row in linked_res.all()}

    rng = random.Random(42)  # deterministik
    links_created = 0
    for p in products:
        if p.id in already_linked:
            continue
        chosen = rng.sample(suppliers, min(rng.randint(1, 2), len(suppliers)))
        for idx, s in enumerate(chosen):
            db.add(
                ProductSupplier(
                    product_id=p.id,
                    supplier_id=s.id,
                    supplier_sku=f"SKU-{p.id}-{s.id}",
                    last_unit_cost=round(p.cost * rng.uniform(0.92, 1.05), 2)
                    if p.cost
                    else None,
                    last_purchase_at=datetime.utcnow()
                    - timedelta(days=rng.randint(3, 60)),
                    lead_time_days=rng.choice([2, 3, 5, 7, 10]),
                    is_preferred=(idx == 0),
                )
            )
            links_created += 1
    await db.flush()
    return {"supplier_links_created": links_created}


# Fiyat değişim sebep havuzu — mantıklı çeşitlilik için
PRICE_REASONS_UP = [
    "Tedarikçi zammı",
    "Maliyet artışı yansıması",
    "Enflasyon güncellemesi",
    "Sezonsal artış",
    "Lojistik maliyetlerindeki artış",
]
PRICE_REASONS_DOWN = [
    "Sezonsal düşüş",
    "Stok eritme kampanyası",
    "Rekabet ayarlaması",
    "Tedarikçi indirimi yansıması",
]
COST_REASONS_UP = [
    "Tedarikçi alış fiyatı arttı",
    "Hammadde maliyeti yükseldi",
    "Yeni alım partisi pahalı geldi",
]
COST_REASONS_DOWN = [
    "Yeni tedarikçiyle daha ucuz alım",
    "Toplu alımda iskonto",
]

# Sezonsal ürünler — fiyat dalgalanması daha yüksek
SEASONAL_PRODUCTS = {"Domates", "Biber", "Salca"}


async def ensure_price_history(db: AsyncSession) -> dict:
    """Her ürün için son ~180 günde 3-5 ara fiyat + maliyet değişimi üret.

    Idempotent: bir üründe PRICE field history sayısı 2'den fazlaysa
    (Ilk olusturma + zaten enrich edilmiş) atlanır.
    """
    res = await db.execute(
        select(Product).where(Product.is_active.is_(True))
    )
    products = list(res.scalars())

    # Mevcut history sayıları
    counts_res = await db.execute(
        select(
            PriceHistory.product_id,
            PriceHistory.field,
            func.count(PriceHistory.id),
        ).group_by(PriceHistory.product_id, PriceHistory.field)
    )
    counts = {(pid, field): n for pid, field, n in counts_res.all()}

    rng = random.Random(123)  # deterministik
    rows_created = 0

    for p in products:
        price_count = counts.get((p.id, PriceHistoryField.PRICE), 0)
        if price_count > 1:
            continue  # zaten enrich edilmiş veya manuel ekleme var

        is_seasonal = p.name in SEASONAL_PRODUCTS

        # Geçmiş başlangıç noktası: bugüne göre %10-25 düşük (genel enflasyon yukarı trend)
        start_price = round(p.price / rng.uniform(1.10, 1.25), 2)
        start_cost = (
            round(p.cost / rng.uniform(1.08, 1.20), 2) if p.cost else 0.0
        )

        # Kaç ara adım?
        n_steps = rng.randint(3, 5)
        # Tarihleri 180 gün içine yay
        step_days = 180 // (n_steps + 1)

        prev_price = start_price
        prev_cost = start_cost

        for step in range(n_steps):
            # Adım: prev → current'a doğru yaklaş, ama her adım küçük rastgele dalgalanma
            progress_remaining = (n_steps - step) / n_steps
            target_price = p.price * (1 - 0.05 * progress_remaining)  # son fiyata yaklaş
            # Sezonsal ürünlerde rastgele +-%10 dalgalanma
            if is_seasonal:
                jitter = rng.uniform(-0.10, 0.10)
                target_price *= 1 + jitter

            new_price = round(target_price, 2)
            # changed_at: 180 - (step + 1) * step_days günler öncesi (+- random)
            days_ago = 180 - (step + 1) * step_days + rng.randint(-7, 7)
            changed_at = datetime.utcnow() - timedelta(days=max(days_ago, 0))

            if abs(new_price - prev_price) > 0.5:
                reason = (
                    rng.choice(PRICE_REASONS_UP)
                    if new_price > prev_price
                    else rng.choice(PRICE_REASONS_DOWN)
                )
                db.add(
                    PriceHistory(
                        product_id=p.id,
                        field=PriceHistoryField.PRICE,
                        old_value=prev_price,
                        new_value=new_price,
                        reason=reason,
                        changed_at=changed_at,
                    )
                )
                rows_created += 1
                prev_price = new_price

            # Maliyet — fiyatla benzer ama daha az volatil
            if p.cost and start_cost > 0:
                target_cost = p.cost * (1 - 0.04 * progress_remaining)
                new_cost = round(target_cost * rng.uniform(0.97, 1.03), 2)
                if abs(new_cost - prev_cost) > 0.3:
                    reason_c = (
                        rng.choice(COST_REASONS_UP)
                        if new_cost > prev_cost
                        else rng.choice(COST_REASONS_DOWN)
                    )
                    db.add(
                        PriceHistory(
                            product_id=p.id,
                            field=PriceHistoryField.COST,
                            old_value=prev_cost,
                            new_value=new_cost,
                            reason=reason_c,
                            changed_at=changed_at,
                        )
                    )
                    rows_created += 1
                    prev_cost = new_cost

        # Son aşama: prev → current_price (mevcut), reason="Güncel fiyat"
        if abs(p.price - prev_price) > 0.5:
            reason_last = (
                rng.choice(PRICE_REASONS_UP)
                if p.price > prev_price
                else rng.choice(PRICE_REASONS_DOWN)
            )
            db.add(
                PriceHistory(
                    product_id=p.id,
                    field=PriceHistoryField.PRICE,
                    old_value=prev_price,
                    new_value=p.price,
                    reason=reason_last,
                    changed_at=datetime.utcnow() - timedelta(days=rng.randint(1, 7)),
                )
            )
            rows_created += 1
        if p.cost and abs(p.cost - prev_cost) > 0.3:
            reason_last_c = (
                rng.choice(COST_REASONS_UP)
                if p.cost > prev_cost
                else rng.choice(COST_REASONS_DOWN)
            )
            db.add(
                PriceHistory(
                    product_id=p.id,
                    field=PriceHistoryField.COST,
                    old_value=prev_cost,
                    new_value=p.cost,
                    reason=reason_last_c,
                    changed_at=datetime.utcnow() - timedelta(days=rng.randint(1, 7)),
                )
            )
            rows_created += 1

    await db.flush()
    return {"price_history_rows_created": rows_created}


# Gider şablonları — her ay tekrarlanır
RECURRING_EXPENSES_MONTHLY = [
    # (category, base_amount, vendor, description, day_of_month, jitter_pct)
    (ExpenseCategory.RENT, 12000.0, "Mülk sahibi", "Aylık dükkân kirası", 1, 0.0),
    (ExpenseCategory.SALARIES, 38000.0, "Bordro", "Personel maaşları", 5, 0.0),
    (ExpenseCategory.UTILITIES, 1800.0, "BEDAŞ", "Elektrik faturası", 15, 0.15),
    (ExpenseCategory.UTILITIES, 650.0, "İSKİ", "Su faturası", 18, 0.10),
    (ExpenseCategory.UTILITIES, 420.0, "Türk Telekom", "İnternet+telefon", 20, 0.05),
    (ExpenseCategory.INSURANCE, 1500.0, "Anadolu Sigorta", "İşyeri sigortası", 10, 0.0),
]

# Aralıklı (her ay olmayan) giderler
SPORADIC_EXPENSES = [
    # (category, base_amount, vendor, description, prob_per_month, jitter_pct)
    (ExpenseCategory.MARKETING, 2500.0, "Sosyal medya ajansı", "Reklam kampanyası", 0.7, 0.4),
    (ExpenseCategory.LOGISTICS, 1200.0, "Yurt İçi Kargo", "Aylık kargo hesabı", 0.85, 0.3),
    (ExpenseCategory.MAINTENANCE, 800.0, "Servis", "Soğutucu bakımı", 0.3, 0.5),
    (ExpenseCategory.SUPPLIES, 600.0, "OfisMix", "Ofis malzemeleri", 0.5, 0.4),
    (ExpenseCategory.TAX, 7500.0, "GİB", "KDV ödemesi", 0.33, 0.0),  # ~3 ayda bir
    (ExpenseCategory.OTHER, 450.0, "Notere", "Çeşitli harçlar", 0.25, 0.3),
]


async def ensure_expenses(db: AsyncSession, months: int = 6) -> dict:
    """Son N ay için gerçekçi gider kayıtları üretir. Idempotent: zaten varsa atlanır."""
    from sqlalchemy import func

    # Zaten gider varsa atla
    count_res = await db.execute(select(func.count(Expense.id)))
    if int(count_res.scalar_one() or 0) > 0:
        return {"expenses_created": 0}

    rng = random.Random(2025)  # deterministik
    today = date.today()
    created = 0

    for m_offset in range(months):
        # Hedef ay başı
        ref = (today.replace(day=1) - timedelta(days=m_offset * 30)).replace(day=1)

        # Tekrar eden aylık giderler
        for category, base, vendor, desc, day, jitter in RECURRING_EXPENSES_MONTHLY:
            try:
                incurred = ref.replace(day=min(day, 28))
            except ValueError:
                incurred = ref
            amount = base * (1 + rng.uniform(-jitter, jitter)) if jitter > 0 else base
            # Aylık enflasyon: eski aylarda biraz daha düşük (3%/ay)
            amount = amount * (1 - 0.03 * m_offset / 12)
            db.add(
                Expense(
                    category=category,
                    amount=round(amount, 2),
                    vendor=vendor,
                    description=desc,
                    incurred_at=datetime.combine(incurred, datetime.min.time())
                    + timedelta(hours=rng.randint(9, 17)),
                    is_recurring=True,
                )
            )
            created += 1

        # Aralıklı giderler
        for category, base, vendor, desc, prob, jitter in SPORADIC_EXPENSES:
            if rng.random() > prob:
                continue
            day = rng.randint(1, 28)
            incurred = ref.replace(day=day)
            amount = base * (1 + rng.uniform(-jitter, jitter))
            amount = amount * (1 - 0.02 * m_offset / 12)
            db.add(
                Expense(
                    category=category,
                    amount=round(amount, 2),
                    vendor=vendor,
                    description=desc,
                    incurred_at=datetime.combine(incurred, datetime.min.time())
                    + timedelta(hours=rng.randint(9, 17)),
                    is_recurring=False,
                )
            )
            created += 1

    await db.flush()
    return {"expenses_created": created}


async def ensure_social_accounts(db: AsyncSession) -> dict:
    """SOCIAL_ACCOUNT_CATALOG'taki hesapları idempotent ekle.

    Eşleştirme: (platform, handle) tek anahtar. Zaten varsa atlanır.
    """
    res = await db.execute(select(SocialAccount))
    existing = {(a.platform, a.handle) for a in res.scalars()}

    created = 0
    for platform_value, handle, display_name, profile_url in SOCIAL_ACCOUNT_CATALOG:
        try:
            platform = SocialPlatform(platform_value)
        except ValueError:
            continue
        if (platform, handle) in existing:
            continue
        db.add(
            SocialAccount(
                platform=platform,
                handle=handle,
                display_name=display_name,
                profile_url=profile_url,
                is_active=True,
            )
        )
        created += 1
    await db.flush()
    return {"social_accounts_created": created}


async def ensure_social_posts(db: AsyncSession) -> dict:
    """SOCIAL_POST_CATALOG'taki örnek postları idempotent ekle.

    Eşleştirme: title alanına göre. Zaten varsa atlanır.
    """
    count_res = await db.execute(select(func.count(SocialPost.id)))
    if int(count_res.scalar_one() or 0) > 0:
        # Zaten en az 1 post var — yine de duplicate olmayanları ekleyelim
        existing_titles_res = await db.execute(select(SocialPost.title))
        existing_titles = {t[0] for t in existing_titles_res.all()}
    else:
        existing_titles = set()

    # Ürünleri ad → id eşle
    prod_res = await db.execute(select(Product))
    products_by_name = {p.name: p for p in prod_res.scalars()}

    created = 0
    now = datetime.utcnow()
    for (
        title,
        content,
        platforms_csv,
        hashtags_csv,
        status_value,
        days_offset,
        product_name,
        ai_generated,
        prompt,
    ) in SOCIAL_POST_CATALOG:
        if title in existing_titles:
            continue
        try:
            status = SocialPostStatus(status_value)
        except ValueError:
            status = SocialPostStatus.DRAFT
        product = products_by_name.get(product_name) if product_name else None

        published_at = None
        scheduled_at = None
        if status == SocialPostStatus.PUBLISHED:
            published_at = now + timedelta(days=days_offset)
        elif status == SocialPostStatus.SCHEDULED:
            scheduled_at = now + timedelta(days=max(days_offset, 1))

        db.add(
            SocialPost(
                title=title,
                content=content,
                target_platforms=platforms_csv,
                hashtags=hashtags_csv,
                status=status,
                scheduled_at=scheduled_at,
                published_at=published_at,
                ai_generated=ai_generated,
                prompt=prompt,
                related_product_id=product.id if product else None,
            )
        )
        created += 1

    await db.flush()
    return {"social_posts_created": created}


async def ensure_supplier_marketplace_meta(db: AsyncSession) -> dict:
    """SUPPLIER_META'daki kategori/kargo/şehir/açıklama/rating'leri SUPPLIER_CATALOG
    sıralı eşleştir. Eksikse ekler; varsa override etmez (idempotent).
    """
    res = await db.execute(select(Supplier))
    suppliers = list(res.scalars())
    by_name = {s.name: s for s in suppliers}

    updated = 0
    for (name, *_), meta in zip(SUPPLIER_CATALOG, SUPPLIER_META, strict=False):
        s = by_name.get(name)
        if s is None:
            continue
        category, carrier, city, district, description, rating = meta
        changed = False
        if not s.category and category:
            s.category = category
            changed = True
        if not s.carrier and carrier:
            s.carrier = carrier
            changed = True
        if not s.city and city:
            s.city = city
            changed = True
        if not s.district and district:
            s.district = district
            changed = True
        if not s.description and description:
            s.description = description
            changed = True
        if s.rating is None and rating is not None:
            s.rating = rating
            changed = True
        if changed:
            updated += 1
    await db.flush()
    return {"supplier_meta_updated": updated}


async def ensure_admin_location(db: AsyncSession) -> dict:
    """Aktif admin'lerden ilki için marketplace varsayılan konum/kargo set et.

    Multi-tenant değiliz; hackathon demosunda ana admin Istanbul'daki bir KOBİ
    olarak temsil ediliyor. Komşu KOBİ verisi de Istanbul'da.
    """
    res = await db.execute(
        select(AdminUser).where(AdminUser.is_active.is_(True)).order_by(AdminUser.id.asc())
    )
    admins = list(res.scalars())
    updated = 0
    for admin in admins:
        changed = False
        if not admin.city:
            admin.city = "Istanbul"
            changed = True
        if not admin.district:
            admin.district = "Kadikoy"
            changed = True
        if not admin.preferred_carrier:
            admin.preferred_carrier = "Yurtici Kargo"
            changed = True
        if changed:
            updated += 1
    await db.flush()
    return {"admin_location_updated": updated}


async def ensure_nearby_shops(db: AsyncSession) -> dict:
    """NEARBY_SHOP_CATALOG'taki mock komşuları idempotent ekle."""
    res = await db.execute(select(NearbyShop))
    existing_names = {s.name for s in res.scalars()}
    created = 0
    for name, shop_type, city, district, distance_km, carrier in NEARBY_SHOP_CATALOG:
        if name in existing_names:
            continue
        db.add(
            NearbyShop(
                name=name,
                shop_type=shop_type,
                city=city,
                district=district,
                distance_km=distance_km,
                preferred_carrier=carrier,
                is_active=True,
            )
        )
        created += 1
    await db.flush()
    return {"nearby_shops_created": created}


async def ensure_nearby_purchases(db: AsyncSession) -> dict:
    """NEARBY_PURCHASE_CATALOG'taki mock satınalmaları ekle.

    İdempotent: eğer hiç purchase yoksa hepsi eklenir, varsa atlanır
    (count tabanlı kısa devre).
    """
    count_res = await db.execute(select(func.count(NearbyShopPurchase.id)))
    if int(count_res.scalar_one() or 0) > 0:
        return {"nearby_purchases_created": 0}

    shop_res = await db.execute(select(NearbyShop))
    shops_by_name = {s.name: s for s in shop_res.scalars()}

    supp_res = await db.execute(select(Supplier))
    suppliers_by_name = {s.name: s for s in supp_res.scalars()}

    created = 0
    for (
        shop_name,
        supplier_name,
        product_name,
        category,
        qty,
        unit_cost,
        carrier,
        days_ago,
    ) in NEARBY_PURCHASE_CATALOG:
        shop = shops_by_name.get(shop_name)
        if shop is None:
            continue
        supplier = (
            suppliers_by_name.get(supplier_name) if supplier_name else None
        )
        db.add(
            NearbyShopPurchase(
                shop_id=shop.id,
                supplier_id=supplier.id if supplier else None,
                product_name=product_name,
                product_category=category,
                quantity=qty,
                unit_cost=unit_cost,
                carrier=carrier,
                purchased_at=datetime.utcnow() - timedelta(days=days_ago),
            )
        )
        created += 1
    await db.flush()
    return {"nearby_purchases_created": created}


async def enrich_all(db: AsyncSession) -> dict:
    """Tüm idempotent zenginleştirmeleri sırayla uygula."""
    result = {}
    result.update(await ensure_warehouses(db))
    result.update(await ensure_suppliers(db))
    result.update(await ensure_supplier_marketplace_meta(db))
    result.update(await ensure_admin_location(db))
    result.update(await ensure_nearby_shops(db))
    result.update(await ensure_nearby_purchases(db))
    result.update(await ensure_product_supplier_links(db))
    result.update(await ensure_multi_warehouse(db))
    # Lot ekleme balance'lara bağlı, multi-warehouse'tan sonra çalışmalı
    result.update(await ensure_lots(db))
    # Fiyat geçmişi — son
    result.update(await ensure_price_history(db))
    # Finansal mock data — son 6 ay giderler
    result.update(await ensure_expenses(db, months=6))
    # Sosyal medya — hesaplar + örnek postlar
    result.update(await ensure_social_accounts(db))
    result.update(await ensure_social_posts(db))
    await db.commit()
    logger.info("Demo enrichment complete: %s", result)
    return result
