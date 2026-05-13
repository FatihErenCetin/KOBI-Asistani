"""Demo enricher — idempotent prod-safe akis."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import products as products_crud
from app.db.models import (
    StockBalance,
    StockLot,
    StockMovementReason,
    Warehouse,
)
from app.main import app
from app.services.demo_enricher import enrich_all
from sqlalchemy import select


@pytest_asyncio.fixture
async def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}


@pytest.mark.asyncio
async def test_enrich_adds_missing_warehouses(db):
    """Conftest sadece default warehouse ekliyor — enrich 3 ek warehouse eklemeli."""
    before = (await db.execute(select(Warehouse))).scalars().all()
    assert len(list(before)) == 1
    result = await enrich_all(db)
    assert result["warehouses_created"] == 3
    after = list((await db.execute(select(Warehouse))).scalars())
    codes = {w.code for w in after}
    assert {"main", "shube", "cold", "vehicle"}.issubset(codes)


@pytest.mark.asyncio
async def test_enrich_is_idempotent(db):
    """İki kez çağrıldığında ikincide hiçbir şey eklenmemeli."""
    r1 = await enrich_all(db)
    assert r1["warehouses_created"] == 3
    r2 = await enrich_all(db)
    assert r2["warehouses_created"] == 0
    assert r2.get("lots_created", 0) == 0


@pytest.mark.asyncio
async def test_enrich_distributes_products_to_multi_warehouse(db):
    p = await products_crud.create(db, name="Peynir", unit="kg", price=200, cost=120)
    await products_crud.adjust_stock(db, p, 10, reason=StockMovementReason.INITIAL)
    # Şu an Peynir tek depoda (default Ana Depo)

    await enrich_all(db)

    bals = list(
        (
            await db.execute(
                select(StockBalance).where(StockBalance.product_id == p.id)
            )
        ).scalars()
    )
    # MULTI_WAREHOUSE_SPLIT'te Peynir → [cold 0.7, main 0.3] → 2 depo
    assert len(bals) >= 2
    # NOT: ensure_orders_history sonradan eklenen sipariş enricher'ı bu
    # ürünü tüketmiş olabilir; toplam ilk yüklemeyi aşmamalı.
    total = sum(b.quantity for b in bals)
    assert 0 <= total <= 10.01


@pytest.mark.asyncio
async def test_enrich_creates_lots(db):
    """LOT_CATALOG'taki ürünler için lot oluşturmali."""
    p = await products_crud.create(db, name="Yogurt", unit="kg", price=60, cost=39)
    await products_crud.adjust_stock(db, p, 35, reason=StockMovementReason.INITIAL)
    await enrich_all(db)

    lots = list(
        (
            await db.execute(select(StockLot).where(StockLot.product_id == p.id))
        ).scalars()
    )
    # LOT_CATALOG'ta Yoğurt için 2 lot tanımlı
    assert len(lots) == 2
    lot_numbers = {lot.lot_number for lot in lots}
    assert "YGT-2510-01" in lot_numbers
    assert "YGT-2510-02" in lot_numbers


@pytest.mark.asyncio
async def test_enrich_endpoint_requires_auth(client):
    r = await client.post("/api/v1/admin/enrich-demo-data")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_enrich_endpoint_returns_summary(client, auth):
    r = await client.post("/api/v1/admin/enrich-demo-data", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert "warehouses_created" in body
    assert "lots_created" in body
    assert "products_split" in body
    assert "suppliers_created" in body
    assert "supplier_links_created" in body
    assert "price_history_rows_created" in body


@pytest.mark.asyncio
async def test_enrich_creates_suppliers(db):
    """SUPPLIER_CATALOG'taki 5 tedarikçi eklenmeli."""
    from sqlalchemy import select
    from app.db.models import Supplier
    from app.services.demo_enricher import enrich_all

    before = list((await db.execute(select(Supplier))).scalars())
    assert len(before) == 0
    await enrich_all(db)
    after = list((await db.execute(select(Supplier))).scalars())
    assert len(after) == 5
    names = {s.name for s in after}
    assert "Anadolu Bal Kooperatifi" in names


@pytest.mark.asyncio
async def test_enrich_creates_product_supplier_links(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    await enrich_all(db)
    from sqlalchemy import select
    from app.db.models import ProductSupplier

    links = list(
        (
            await db.execute(
                select(ProductSupplier).where(ProductSupplier.product_id == p.id)
            )
        ).scalars()
    )
    assert len(links) >= 1
    # Bir tane preferred olmalı
    assert any(l.is_preferred for l in links)


@pytest.mark.asyncio
async def test_enrich_creates_price_history(db):
    """Her ürün için en az 3 PriceHistory satırı (PRICE field)."""
    from sqlalchemy import func, select
    from app.db.models import PriceHistory, PriceHistoryField

    p = await products_crud.create(db, name="Bal", unit="kg", price=280, cost=180)
    # 'Ilk olusturma' history zaten var, sayısını ölç
    before_res = await db.execute(
        select(func.count(PriceHistory.id)).where(
            PriceHistory.product_id == p.id,
            PriceHistory.field == PriceHistoryField.PRICE,
        )
    )
    before = before_res.scalar_one()
    await enrich_all(db)
    after_res = await db.execute(
        select(func.count(PriceHistory.id)).where(
            PriceHistory.product_id == p.id,
            PriceHistory.field == PriceHistoryField.PRICE,
        )
    )
    after = after_res.scalar_one()
    assert after >= before + 3  # en az 3 yeni adım


@pytest.mark.asyncio
async def test_price_history_idempotent(db):
    """İkinci kez enrich çağrılınca yeni PRICE history eklenmemeli."""
    from sqlalchemy import func, select
    from app.db.models import PriceHistory

    await products_crud.create(db, name="Bal", unit="kg", price=280, cost=180)
    await enrich_all(db)
    count1 = (
        await db.execute(select(func.count(PriceHistory.id)))
    ).scalar_one()
    await enrich_all(db)
    count2 = (
        await db.execute(select(func.count(PriceHistory.id)))
    ).scalar_one()
    assert count2 == count1
