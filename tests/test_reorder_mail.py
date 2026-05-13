"""M9: Auto-reorder mail draft."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import suppliers as suppliers_crud
from app.main import app
from app.services.mail_template import draft_reorder_mail, format_tr_amount


def test_tr_amount_format():
    assert format_tr_amount(1234.5) == "1.234,50 TL"
    assert format_tr_amount(0) == "0,00 TL"


def test_draft_text_contains_key_info():
    out = draft_reorder_mail(
        supplier_name="Bal Tedarikçisi",
        product_name="Bal",
        order_qty=10,
        unit="kg",
        last_unit_cost=50,
        lead_time_days=3,
        admin_name="Ahmet",
    )
    assert "Bal Tedarikçisi" in out["body"]
    assert "10 kg" in out["body"]
    assert "Ahmet" in out["body"]
    assert "3 gün" in out["body"]


def test_draft_without_cost_lead_skips_them():
    out = draft_reorder_mail(
        supplier_name="X",
        product_name="Bal",
        order_qty=5,
        unit="kg",
    )
    assert "maliyet" not in out["body"].lower()
    assert "teslim süresi" not in out["body"].lower()


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
async def test_endpoint_uses_preferred_supplier(client, auth, db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    s1 = await suppliers_crud.create(db, name="A", email="a@x.com")
    s2 = await suppliers_crud.create(db, name="B", email="b@x.com")
    await ps_crud.add_link(
        db, product_id=p.id, supplier_id=s1.id, last_unit_cost=45, lead_time_days=5,
    )
    await ps_crud.add_link(
        db, product_id=p.id, supplier_id=s2.id, last_unit_cost=40,
        lead_time_days=7, is_preferred=True,
    )
    await db.commit()

    r = await client.post(
        "/api/v1/reorder/draft-mail",
        json={"product_id": p.id, "order_qty": 20},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "B" in body["body"]  # preferred B
    assert body["supplier_email"] == "b@x.com"
    assert "20 kg" in body["body"]


@pytest.mark.asyncio
async def test_endpoint_no_supplier_400(client, auth, db):
    p = await products_crud.create(db, name="Yok", unit="kg", price=10, cost=5)
    await db.commit()
    r = await client.post(
        "/api/v1/reorder/draft-mail",
        json={"product_id": p.id, "order_qty": 5},
        headers=auth,
    )
    assert r.status_code == 400
