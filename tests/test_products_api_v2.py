import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.main import app


@pytest_asyncio.fixture
async def client(db):
    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"Authorization": f"Bearer {settings.ADMIN_TOKEN}"}


@pytest.mark.asyncio
async def test_create_update_get_detail(client, auth):
    r = await client.post(
        "/api/v1/products",
        json={
            "name": "TEST_API_PROD",
            "unit": "kg",
            "price": 100,
            "cost": 60,
            "stock": 5,
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    pid = body["id"]
    assert body["profit_margin_pct"] == 40.0

    r2 = await client.patch(
        f"/api/v1/products/{pid}",
        json={"price": 120, "reason": "Test artis"},
        headers=auth,
    )
    assert r2.status_code == 200
    assert r2.json()["price"] == 120

    r3 = await client.get(
        f"/api/v1/products/{pid}/price-history", headers=auth,
    )
    assert r3.status_code == 200
    # initial price + initial cost + update price = 3
    assert len(r3.json()) >= 3

    r4 = await client.get(f"/api/v1/products/{pid}/analytics", headers=auth)
    assert r4.status_code == 200

    r5 = await client.get(
        f"/api/v1/products/{pid}/sparkline?days=7", headers=auth,
    )
    assert r5.status_code == 200
    assert len(r5.json()) == 7


@pytest.mark.asyncio
async def test_stock_movement_endpoint(client, auth):
    r = await client.post(
        "/api/v1/products",
        json={"name": "TEST_STOCK_MV", "unit": "kg", "price": 50, "cost": 30},
        headers=auth,
    )
    pid = r.json()["id"]

    r2 = await client.post(
        f"/api/v1/products/{pid}/stock-movements",
        json={"delta": 5, "reason": "purchase", "note": "test alim"},
        headers=auth,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["stock"] == 5

    r3 = await client.get(
        f"/api/v1/products/{pid}/movements", headers=auth,
    )
    assert r3.status_code == 200
    assert any(m["reason"] == "purchase" for m in r3.json())


@pytest.mark.asyncio
async def test_supplier_link_lifecycle(client, auth):
    p = await client.post(
        "/api/v1/products",
        json={"name": "TEST_LINK_PROD", "unit": "kg", "price": 50, "cost": 30},
        headers=auth,
    )
    pid = p.json()["id"]
    s = await client.post(
        "/api/v1/suppliers", json={"name": "TEST_LINK_SUPP"}, headers=auth,
    )
    sid = s.json()["id"]

    r = await client.post(
        f"/api/v1/products/{pid}/suppliers",
        json={"supplier_id": sid, "last_unit_cost": 25.0, "is_preferred": True},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    ll = await client.get(
        f"/api/v1/products/{pid}/suppliers", headers=auth,
    )
    assert any(
        l["supplier_id"] == sid and l["is_preferred"] for l in ll.json()
    )

    r2 = await client.patch(
        f"/api/v1/products/{pid}/suppliers/{sid}",
        json={"lead_time_days": 5},
        headers=auth,
    )
    assert r2.status_code == 200
    assert r2.json()["lead_time_days"] == 5

    r3 = await client.delete(
        f"/api/v1/products/{pid}/suppliers/{sid}", headers=auth,
    )
    assert r3.status_code == 204


@pytest.mark.asyncio
async def test_soft_delete_product(client, auth):
    r = await client.post(
        "/api/v1/products",
        json={"name": "TEST_DEL_PROD", "unit": "kg", "price": 10},
        headers=auth,
    )
    pid = r.json()["id"]
    r2 = await client.delete(f"/api/v1/products/{pid}", headers=auth)
    assert r2.status_code == 204
    # default list'te yok
    rl = await client.get("/api/v1/products", headers=auth)
    assert all(p["id"] != pid for p in rl.json())
