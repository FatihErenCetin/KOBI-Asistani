"""Auth endpoint tests using httpx AsyncClient (same event loop as fixtures)."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import admin_users as admin_crud
from app.main import app


@pytest_asyncio.fixture
async def client(db):
    """AsyncClient with get_db overridden to use the test session fixture."""

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db):
    user = await admin_crud.create(
        db,
        email="test@example.com",
        password="correct-horse-battery",
        name="Test Admin",
    )
    await db.commit()
    return user


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "correct-horse-battery"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test Admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client, admin_user):
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client, db, admin_user):
    admin_user.is_active = False
    await db.flush()
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "correct-horse-battery"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client, admin_user):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "correct-horse-battery"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_without_token(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_with_garbage_token(client):
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-jwt"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_admin_token(client):
    """Legacy: ADMIN_TOKEN env de hala calismali."""
    r = await client.get(
        "/api/v1/dashboard/today",
        headers={"Authorization": f"Bearer {settings.ADMIN_TOKEN}"},
    )
    # 200 (data var) veya 500 (boş test DB) olabilir — ama 401/403 olmamalı
    assert r.status_code not in (401, 403)


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_jwt(client, admin_user):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "correct-horse-battery"},
    )
    token = login.json()["access_token"]
    r = await client.get(
        "/api/v1/dashboard/today", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code not in (401, 403)


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_bad_token(client):
    r = await client.get(
        "/api/v1/dashboard/today", headers={"Authorization": "Bearer invalid"}
    )
    assert r.status_code in (401, 403)
