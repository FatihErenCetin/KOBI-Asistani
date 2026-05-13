"""M4: bulk sparkline endpoint + revenue historical accuracy."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import product_analytics as analytics
from app.db.crud import products as products_crud
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
async def test_bulk_sparklines_returns_per_product(db):
    p1 = await products_crud.create(db, name="A", unit="kg", price=10, cost=5)
    p2 = await products_crud.create(db, name="B", unit="kg", price=10, cost=5)
    out = await analytics.bulk_sparklines(db, [p1.id, p2.id], days=7)
    assert p1.id in out and p2.id in out
    assert len(out[p1.id]) == 7
    assert len(out[p2.id]) == 7
    assert all("day" in pt and "units" in pt for pt in out[p1.id])


@pytest.mark.asyncio
async def test_bulk_sparkline_endpoint(client, auth, db):
    p1 = await products_crud.create(db, name="A", unit="kg", price=10, cost=5)
    p2 = await products_crud.create(db, name="B", unit="kg", price=10, cost=5)
    await db.commit()

    r = await client.get(
        f"/api/v1/products/sparklines?ids={p1.id},{p2.id}&days=7", headers=auth
    )
    assert r.status_code == 200, r.text
    body = r.json()
    # JSON anahtarları string olarak gelir
    assert str(p1.id) in body
    assert str(p2.id) in body
    assert len(body[str(p1.id)]) == 7


@pytest.mark.asyncio
async def test_revenue_uses_historical_unit_price(db):
    """Fiyat degisirse, gecmis ciro eski fiyatla hesaplanmali."""
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    await products_crud.adjust_stock(db, p, 30, reason=StockMovementReason.INITIAL)
    c = await customers_crud.create(db, name="X")
    # Satış: 2 kg × 100 TL = 200 TL
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 2.0)])
    # Şimdi fiyatı arttır
    await products_crud.update(db, p, price=150)
    await db.commit()

    data = await analytics.for_product(db, p)
    # Eski (yanlış) hesap: 2 × 150 = 300
    # Yeni (doğru) hesap: 2 × 100 = 200 (OrderItem.unit_price'tan)
    assert data["revenue_30d"] == 200.0


@pytest.mark.asyncio
async def test_bulk_sparkline_max_ids_limit(client, auth):
    ids = ",".join(str(i) for i in range(1, 250))
    r = await client.get(f"/api/v1/products/sparklines?ids={ids}", headers=auth)
    assert r.status_code == 400
