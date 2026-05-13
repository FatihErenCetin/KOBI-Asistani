"""M13: Complaint risk."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import complaints as complaints_crud
from app.main import app
from app.services.risk_classifier import detect_signals


def test_detect_signals_empty_text():
    assert detect_signals("merhaba siparis ne durumda") == []


def test_detect_signals_complaint():
    sigs = detect_signals("ürün bozuk, iade istiyorum")
    assert len(sigs) >= 2  # bozuk + iade


def test_detect_signals_case_insensitive():
    sigs = detect_signals("REZALET, KOTU bir hizmet")
    assert len(sigs) >= 1


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
async def test_create_and_list_complaint(client, auth, db):
    await complaints_crud.create(
        db,
        customer_id=None,
        telegram_user_id=12345,
        message_text="iade istiyorum",
        risk_score=0.85,
        signals=["iade"],
    )
    await db.commit()
    r = await client.get("/api/v1/complaints", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert any(c["telegram_user_id"] == 12345 for c in rows)


@pytest.mark.asyncio
async def test_resolve_complaint(client, auth, db):
    c = await complaints_crud.create(
        db, customer_id=None, telegram_user_id=999,
        message_text="...", risk_score=0.8, signals=[],
    )
    await db.commit()
    r = await client.post(f"/api/v1/complaints/{c.id}/resolve", headers=auth)
    assert r.status_code == 200
    assert r.json()["resolved"] is True
    # list_open'da artık yok
    rl = await client.get("/api/v1/complaints", headers=auth)
    assert all(row["id"] != c.id for row in rl.json())
