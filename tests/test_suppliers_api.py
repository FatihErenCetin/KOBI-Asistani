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
async def test_create_and_get_supplier(client, auth):
    r = await client.post(
        "/api/v1/suppliers",
        json={"name": "TEST_API_SUPP", "phone": "+90000"},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    r2 = await client.get(f"/api/v1/suppliers/{sid}", headers=auth)
    assert r2.status_code == 200
    assert r2.json()["name"] == "TEST_API_SUPP"


@pytest.mark.asyncio
async def test_list_requires_auth(client):
    r = await client.get("/api/v1/suppliers")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_patch_supplier(client, auth):
    r = await client.post(
        "/api/v1/suppliers", json={"name": "TEST_PATCH"}, headers=auth,
    )
    sid = r.json()["id"]
    r2 = await client.patch(
        f"/api/v1/suppliers/{sid}",
        json={"phone": "+905550000000"},
        headers=auth,
    )
    assert r2.status_code == 200
    assert r2.json()["phone"] == "+905550000000"


@pytest.mark.asyncio
async def test_delete_supplier_soft(client, auth):
    r = await client.post(
        "/api/v1/suppliers", json={"name": "TEST_DEL"}, headers=auth,
    )
    sid = r.json()["id"]
    r2 = await client.delete(f"/api/v1/suppliers/{sid}", headers=auth)
    assert r2.status_code == 204
    # default list'te yok
    rl = await client.get("/api/v1/suppliers", headers=auth)
    assert all(s["id"] != sid for s in rl.json())
    # include_inactive=true ile var
    rl2 = await client.get(
        "/api/v1/suppliers?include_inactive=true", headers=auth,
    )
    assert any(s["id"] == sid for s in rl2.json())
