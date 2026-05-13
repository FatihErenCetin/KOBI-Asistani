"""Sosyal medya modülü için endpoint + agent + provider testleri."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.agents import social_media_agent
from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from app.services import media_generators


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


# ---------- Templates & Accounts ----------


@pytest.mark.asyncio
async def test_templates_endpoint_returns_list(client, auth):
    r = await client.get("/api/v1/social/templates", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 5
    ids = {t["id"] for t in rows}
    # Beklenen şablonlardan en az birkaçı olmalı
    assert "indirim" in ids
    assert "yeni_urun" in ids


@pytest.mark.asyncio
async def test_account_crud_roundtrip(client, auth):
    # Create
    r = await client.post(
        "/api/v1/social/accounts",
        json={
            "platform": "instagram",
            "handle": "@kobimarket",
            "display_name": "KOBİ Market",
            "profile_url": "https://instagram.com/kobimarket",
        },
        headers=auth,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["handle"] == "kobimarket"  # '@' soyulmuş olmalı
    assert body["platform"] == "instagram"
    acc_id = body["id"]

    # List
    r = await client.get("/api/v1/social/accounts", headers=auth)
    assert r.status_code == 200
    assert any(a["id"] == acc_id for a in r.json())

    # Patch
    r = await client.patch(
        f"/api/v1/social/accounts/{acc_id}",
        json={"display_name": "Yeni Ad"},
        headers=auth,
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Yeni Ad"

    # Delete (soft)
    r = await client.delete(
        f"/api/v1/social/accounts/{acc_id}", headers=auth
    )
    assert r.status_code == 204

    # Default list excludes soft-deleted
    r = await client.get("/api/v1/social/accounts", headers=auth)
    assert not any(a["id"] == acc_id for a in r.json())

    # include_inactive=true gösterir
    r = await client.get(
        "/api/v1/social/accounts?include_inactive=true", headers=auth
    )
    assert any(a["id"] == acc_id for a in r.json())


@pytest.mark.asyncio
async def test_account_unknown_platform_returns_400(client, auth):
    r = await client.post(
        "/api/v1/social/accounts",
        json={"platform": "myspace", "handle": "kobi"},
        headers=auth,
    )
    assert r.status_code == 400


# ---------- Posts ----------


@pytest.mark.asyncio
async def test_post_crud_and_status_transition(client, auth):
    # Create
    r = await client.post(
        "/api/v1/social/posts",
        json={
            "content": "Bugün indirim var!",
            "target_platforms": ["instagram"],
            "hashtags": ["#indirim", "#kobi"],
        },
        headers=auth,
    )
    assert r.status_code == 201
    body = r.json()
    pid = body["id"]
    assert body["status"] == "draft"
    assert body["target_platforms"] == ["instagram"]
    assert "#indirim" in body["hashtags"]

    # Get
    r = await client.get(f"/api/v1/social/posts/{pid}", headers=auth)
    assert r.status_code == 200

    # Patch status via update (e.g. schedule)
    r = await client.patch(
        f"/api/v1/social/posts/{pid}",
        json={"status": "scheduled"},
        headers=auth,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "scheduled"

    # List status filter
    r = await client.get(
        "/api/v1/social/posts?status=scheduled", headers=auth
    )
    assert any(p["id"] == pid for p in r.json())

    # Publish stub
    r = await client.post(
        f"/api/v1/social/posts/{pid}/publish", headers=auth
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "published"
    assert body["published_at"] is not None

    # Delete
    r = await client.delete(f"/api/v1/social/posts/{pid}", headers=auth)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_publish_without_platforms_rejected(client, auth):
    r = await client.post(
        "/api/v1/social/posts",
        json={"content": "x", "target_platforms": []},
        headers=auth,
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    r = await client.post(
        f"/api/v1/social/posts/{pid}/publish", headers=auth
    )
    assert r.status_code == 400


# ---------- AI Draft ----------


@pytest.mark.asyncio
async def test_draft_endpoint_uses_fallback_without_llm(client, auth):
    """Gemini yoksa deterministik fallback çalışmalı, 200 dönmeli."""
    # Forced fallback: model yoksa zaten _fallback_draft kullanılıyor.
    r = await client.post(
        "/api/v1/social/draft",
        json={
            "prompt": "Bal kampanyası",
            "discount_pct": 15,
            "target_platforms": ["instagram"],
        },
        headers=auth,
    )
    assert r.status_code == 200
    body = r.json()
    assert "content" in body
    assert isinstance(body["hashtags"], list)
    assert "image_prompt" in body


@pytest.mark.asyncio
async def test_fallback_draft_includes_discount_phrase():
    """Birim test: indirim verildiğinde fallback içerikte yüzde geçmeli."""
    out = social_media_agent._fallback_draft(
        prompt="Yeni ürün tanıtımı",
        product_name="Bal",
        product_description="Doğal çiçek balı",
        discount_pct=20,
        target_platforms=["instagram", "tiktok"],
    )
    assert "%20" in out["content"]
    assert out["suggested_platforms"] == ["instagram", "tiktok"]
    assert any("#" in tag for tag in out["hashtags"])


# ---------- Asset generation (provider stub) ----------


@pytest.mark.asyncio
async def test_generate_image_asset_stub_returns_placeholder_url(client, auth):
    """Placeholder provider URL üretmeli + asset READY kaydedilmeli."""
    r = await client.post(
        "/api/v1/social/posts",
        json={"content": "Test", "target_platforms": ["instagram"]},
        headers=auth,
    )
    pid = r.json()["id"]

    r = await client.post(
        f"/api/v1/social/posts/{pid}/assets",
        json={"asset_type": "image", "prompt": "bal kavanozu"},
        headers=auth,
    )
    assert r.status_code == 200
    asset = r.json()
    assert asset["asset_type"] == "image"
    assert asset["status"] == "ready"
    assert asset["url"] and asset["url"].startswith("http")
    assert asset["provider"] == "placeholder"


@pytest.mark.asyncio
async def test_generate_video_asset_returns_pending_when_not_configured(
    client, auth
):
    """Video provider API yokken FAILED durumunda dönmeli, ama 200."""
    r = await client.post(
        "/api/v1/social/posts",
        json={"content": "Video test", "target_platforms": ["youtube"]},
        headers=auth,
    )
    pid = r.json()["id"]

    r = await client.post(
        f"/api/v1/social/posts/{pid}/assets",
        json={"asset_type": "video", "prompt": "tarhana çorbası"},
        headers=auth,
    )
    assert r.status_code == 200
    asset = r.json()
    assert asset["asset_type"] == "video"
    # Placeholder video provider URL üretmez → failed
    assert asset["status"] in {"failed", "pending"}


@pytest.mark.asyncio
async def test_placeholder_image_generator_deterministic_for_same_prompt():
    """Aynı prompt aynı URL üretsin (seed davranışı)."""
    gen = media_generators.PlaceholderImageGenerator()
    a = await gen.generate("bal kavanozu")
    b = await gen.generate("bal kavanozu")
    assert a["url"] == b["url"]
    c = await gen.generate("zeytinyağı şişesi")
    assert c["url"] != a["url"]


# ---------- Auth ----------


@pytest.mark.asyncio
async def test_social_endpoints_require_auth(client):
    r = await client.get("/api/v1/social/accounts")
    assert r.status_code == 401
    r = await client.get("/api/v1/social/posts")
    assert r.status_code == 401
