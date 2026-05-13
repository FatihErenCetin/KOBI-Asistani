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
    total = sum(b.quantity for b in bals)
    assert abs(total - 10) < 0.01  # toplam korundu


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
