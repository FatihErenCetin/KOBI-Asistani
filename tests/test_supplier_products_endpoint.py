"""M2: GET /suppliers/{id}/products endpoint."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
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
async def test_unknown_supplier_returns_404(client, auth):
    r = await client.get("/api/v1/suppliers/999999/products", headers=auth)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_lists_linked_products_preferred_first(client, auth):
    s = await client.post(
        "/api/v1/suppliers", json={"name": "SP_TEST"}, headers=auth
    )
    sid = s.json()["id"]

    # 2 ürün oluştur + linkle, ikincisi preferred
    p1 = await client.post(
        "/api/v1/products",
        json={"name": "P1", "unit": "kg", "price": 10, "cost": 5},
        headers=auth,
    )
    p2 = await client.post(
        "/api/v1/products",
        json={"name": "P2", "unit": "kg", "price": 20, "cost": 10},
        headers=auth,
    )
    pid1, pid2 = p1.json()["id"], p2.json()["id"]
    await client.post(
        f"/api/v1/products/{pid1}/suppliers",
        json={"supplier_id": sid, "supplier_sku": "A", "lead_time_days": 5},
        headers=auth,
    )
    await client.post(
        f"/api/v1/products/{pid2}/suppliers",
        json={"supplier_id": sid, "supplier_sku": "B", "is_preferred": True},
        headers=auth,
    )

    r = await client.get(f"/api/v1/suppliers/{sid}/products", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    # preferred önce
    assert rows[0]["product_id"] == pid2
    assert rows[0]["is_preferred"] is True
    assert rows[0]["supplier_sku"] == "B"


@pytest.mark.asyncio
async def test_requires_auth(client):
    r = await client.get("/api/v1/suppliers/1/products")
    assert r.status_code == 401
