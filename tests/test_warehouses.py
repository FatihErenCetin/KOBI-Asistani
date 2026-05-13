"""M6: Warehouse + StockBalance — per-warehouse stock + Product.stock cache."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.crud import stock_balances as sb_crud
from app.db.crud import warehouses as warehouses_crud
from app.db.models import StockMovementReason
from app.main import app


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
async def test_default_warehouse_exists(db):
    """Fixture default warehouse oluşturuyor."""
    w = await sb_crud.get_default_warehouse(db)
    assert w is not None
    assert w.is_default is True


@pytest.mark.asyncio
async def test_create_warehouse(client, auth):
    r = await client.post(
        "/api/v1/warehouses",
        json={"name": "Şube Depo", "code": "shube", "is_default": False},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "Şube Depo"


@pytest.mark.asyncio
async def test_only_one_default(client, auth, db):
    # Yeni default ekleyince mevcut kapanır
    r = await client.post(
        "/api/v1/warehouses",
        json={"name": "İkinci Ana", "is_default": True},
        headers=auth,
    )
    assert r.status_code == 201
    rows = await warehouses_crud.list_all(db)
    defaults = [w for w in rows if w.is_default]
    assert len(defaults) == 1
    assert defaults[0].name == "İkinci Ana"


@pytest.mark.asyncio
async def test_cannot_delete_default(client, auth, db):
    default = await sb_crud.get_default_warehouse(db)
    r = await client.delete(f"/api/v1/warehouses/{default.id}", headers=auth)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_stock_movement_updates_balance_and_cache(db):
    """record() hem StockBalance hem Product.stock cache'i guncellr."""
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    await products_crud.adjust_stock(db, p, 20, reason=StockMovementReason.INITIAL)

    # Product.stock cache'i 20 olmalı
    assert p.stock == 20.0

    # StockBalance default warehouse'ta 20 olmalı
    default = await sb_crud.get_default_warehouse(db)
    total = await sb_crud.total_for_product(db, p.id)
    assert total == 20.0

    # Satış: 5 kg düşer
    c = await customers_crud.create(db, name="X")
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 5.0)])
    assert p.stock == 15.0
    total = await sb_crud.total_for_product(db, p.id)
    assert total == 15.0


@pytest.mark.asyncio
async def test_multi_warehouse_split(db):
    """İki depoda farklı stoklar — toplam Product.stock = SUM."""
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    sube = await warehouses_crud.create(db, name="Şube", code="s1")

    await products_crud.adjust_stock(
        db, p, 10, reason=StockMovementReason.INITIAL, warehouse_id=default.id
    )
    await products_crud.adjust_stock(
        db, p, 7, reason=StockMovementReason.PURCHASE, warehouse_id=sube.id
    )

    # Toplam 17
    assert p.stock == 17.0
    rows = await sb_crud.breakdown_for_product(db, p.id)
    by_wh = {r.warehouse_id: r.quantity for r in rows}
    assert by_wh[default.id] == 10
    assert by_wh[sube.id] == 7


@pytest.mark.asyncio
async def test_product_warehouse_breakdown_endpoint(client, auth, db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    await products_crud.adjust_stock(db, p, 5, reason=StockMovementReason.INITIAL)
    await db.commit()

    r = await client.get(f"/api/v1/products/{p.id}/warehouses", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["quantity"] == 5.0
