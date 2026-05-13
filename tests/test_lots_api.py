"""M7: Lot endpoint testleri."""

from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import products as products_crud
from app.db.crud import stock_balances as sb_crud
from app.db.crud import stock_lots as lots_crud
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
async def test_create_lot_endpoint_increases_stock(client, auth, db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    await db.commit()
    default = await sb_crud.get_default_warehouse(db)

    r = await client.post(
        f"/api/v1/products/{p.id}/lots",
        json={
            "warehouse_id": default.id,
            "lot_number": "L001",
            "quantity": 10,
            "expiry_date": (date.today() + timedelta(days=20)).isoformat(),
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["lot_number"] == "L001"

    # Lot listesi
    r2 = await client.get(f"/api/v1/products/{p.id}/lots", headers=auth)
    assert len(r2.json()) == 1

    # Stok cache güncellendi
    await db.refresh(p)
    assert p.stock == 10.0


@pytest.mark.asyncio
async def test_expiring_endpoint(client, auth, db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    default = await sb_crud.get_default_warehouse(db)
    await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="X",
        quantity=2,
        expiry_date=date.today() + timedelta(days=5),
    )
    await db.commit()

    r = await client.get("/api/v1/products/expiring?within_days=14", headers=auth)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert any(
        row["product_name"] == "Bal" and row["days_left"] == 5 for row in rows
    )
