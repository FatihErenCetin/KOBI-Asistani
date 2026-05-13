"""M1: JWT'den admin id'yi PriceHistory/StockMovement'a tasiyan akis."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import admin_users as admin_crud
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


@pytest_asyncio.fixture
async def admin_user(db):
    user = await admin_crud.create(
        db, email="auditor@test.com", password="strongpass1", name="Audit Test"
    )
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_jwt_user_records_admin_id_on_create(client, admin_user, db):
    """JWT ile create → price_history.changed_by_admin_id dolu."""
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "auditor@test.com", "password": "strongpass1"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/products",
        json={"name": "AuditProd", "unit": "kg", "price": 100, "cost": 50},
        headers=h,
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r2 = await client.get(f"/api/v1/products/{pid}/price-history", headers=h)
    rows = r2.json()
    assert any(
        row["changed_by_admin_id"] == admin_user.id
        and row["changed_by_admin_name"] == "Audit Test"
        for row in rows
    )


@pytest.mark.asyncio
async def test_jwt_user_records_admin_id_on_price_update(client, admin_user):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "auditor@test.com", "password": "strongpass1"},
    )
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/products",
        json={"name": "AuditProd2", "unit": "kg", "price": 50, "cost": 25},
        headers=h,
    )
    pid = r.json()["id"]

    r2 = await client.patch(
        f"/api/v1/products/{pid}",
        json={"price": 60, "reason": "Sezon"},
        headers=h,
    )
    assert r2.status_code == 200

    r3 = await client.get(f"/api/v1/products/{pid}/price-history", headers=h)
    rows = r3.json()
    update_row = next((r for r in rows if r["old_value"] == 50), None)
    assert update_row is not None
    assert update_row["changed_by_admin_id"] == admin_user.id
    assert update_row["changed_by_admin_name"] == "Audit Test"
    assert update_row["reason"] == "Sezon"


@pytest.mark.asyncio
async def test_admin_token_legacy_leaves_admin_null(client):
    """ADMIN_TOKEN ile yapilan islemler audit'te 'Sistem' kalir."""
    h = {"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}
    r = await client.post(
        "/api/v1/products",
        json={"name": "LegacyProd", "unit": "kg", "price": 100, "cost": 50},
        headers=h,
    )
    assert r.status_code == 201
    pid = r.json()["id"]

    r2 = await client.get(f"/api/v1/products/{pid}/price-history", headers=h)
    rows = r2.json()
    assert all(row["changed_by_admin_id"] is None for row in rows)
    assert all(row["changed_by_admin_name"] is None for row in rows)


@pytest.mark.asyncio
async def test_stock_movement_records_admin(client, admin_user):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "auditor@test.com", "password": "strongpass1"},
    )
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/products",
        json={"name": "StockAuditProd", "unit": "kg", "price": 50, "cost": 25},
        headers=h,
    )
    pid = r.json()["id"]

    r2 = await client.post(
        f"/api/v1/products/{pid}/stock-movements",
        json={"delta": 10, "reason": "purchase", "note": "test"},
        headers=h,
    )
    assert r2.status_code == 200

    r3 = await client.get(f"/api/v1/products/{pid}/movements", headers=h)
    rows = r3.json()
    purchase = next((r for r in rows if r["reason"] == "purchase"), None)
    assert purchase is not None
    assert purchase["created_by_admin_id"] == admin_user.id
    assert purchase["created_by_admin_name"] == "Audit Test"
