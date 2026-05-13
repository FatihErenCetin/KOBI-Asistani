"""Financial analytics testleri."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import customers as customers_crud
from app.db.crud import expenses as expenses_crud
from app.db.crud import financial_analytics as fin
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.models import ExpenseCategory
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
async def test_period_summary_basic(db):
    """Sipariş + gider durumunda revenue/cogs/opex/net hesaplanır."""
    p = await products_crud.create(db, name="P", unit="kg", price=100, cost=60)
    c = await customers_crud.create(db, name="X")
    # 2 kg satış = 200 TL revenue, 120 TL COGS, 80 TL brut kar
    await orders_crud.create_order(db, customer_id=c.id, items=[(p, 2)])
    # 50 TL gider
    await expenses_crud.create(
        db, category=ExpenseCategory.UTILITIES, amount=50, vendor="x"
    )
    await db.commit()

    s = await fin.period_summary(db, since_days=7)
    assert s["revenue"] == 200.0
    assert s["cogs"] == 120.0
    assert s["gross_profit"] == 80.0
    assert s["operating_expenses"] == 50.0
    assert s["net_profit"] == 30.0
    assert s["gross_margin_pct"] == 40.0  # 80/200
    assert s["net_margin_pct"] == 15.0  # 30/200


@pytest.mark.asyncio
async def test_period_summary_no_orders(db):
    """Hiç sipariş yok → revenue 0, marj 0."""
    s = await fin.period_summary(db, since_days=30)
    assert s["revenue"] == 0
    assert s["gross_margin_pct"] == 0


@pytest.mark.asyncio
async def test_category_breakdown(db):
    await expenses_crud.create(
        db, category=ExpenseCategory.RENT, amount=10000
    )
    await expenses_crud.create(
        db, category=ExpenseCategory.SALARIES, amount=30000
    )
    await expenses_crud.create(
        db, category=ExpenseCategory.UTILITIES, amount=2000
    )
    await db.commit()

    rows = await fin.category_breakdown(db, since_days=30)
    # Sıralı: en yüksek önce → salaries
    assert rows[0]["category"] == "salaries"
    assert rows[0]["total"] == 30000.0
    # Toplam pay 100
    assert sum(r["share_pct"] for r in rows) == pytest.approx(100, abs=0.5)


@pytest.mark.asyncio
async def test_top_products_by_profit(db):
    p1 = await products_crud.create(db, name="A", unit="kg", price=200, cost=100)
    p2 = await products_crud.create(db, name="B", unit="kg", price=50, cost=45)
    c = await customers_crud.create(db, name="X")
    # A: 5 kg × 200 = 1000 revenue, 500 cogs → 500 profit
    await orders_crud.create_order(db, customer_id=c.id, items=[(p1, 5)])
    # B: 10 kg × 50 = 500 revenue, 450 cogs → 50 profit
    await orders_crud.create_order(db, customer_id=c.id, items=[(p2, 10)])
    await db.commit()

    rows = await fin.top_products_by_profit(db, since_days=7)
    assert rows[0]["name"] == "A"
    assert rows[0]["gross_profit"] == 500.0
    assert rows[1]["name"] == "B"


@pytest.mark.asyncio
async def test_monthly_trend_returns_n_months(db):
    rows = await fin.monthly_trend(db, months=3)
    assert len(rows) == 3
    # Eskiden yeniye sıralı (YYYY-MM)
    assert rows[0]["month"] <= rows[-1]["month"]


@pytest.mark.asyncio
async def test_expense_crud_endpoints(client, auth):
    r = await client.post(
        "/api/v1/finance/expenses",
        json={
            "category": "rent",
            "amount": 12000,
            "vendor": "Ev sahibi",
            "description": "Mayıs kirası",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    eid = r.json()["id"]

    rl = await client.get("/api/v1/finance/expenses", headers=auth)
    assert any(e["id"] == eid for e in rl.json())

    rp = await client.patch(
        f"/api/v1/finance/expenses/{eid}",
        json={"amount": 13000},
        headers=auth,
    )
    assert rp.status_code == 200
    assert rp.json()["amount"] == 13000

    rd = await client.delete(f"/api/v1/finance/expenses/{eid}", headers=auth)
    assert rd.status_code == 204


@pytest.mark.asyncio
async def test_summary_endpoint(client, auth):
    r = await client.get("/api/v1/finance/summary?since_days=30", headers=auth)
    assert r.status_code == 200
    body = r.json()
    assert "revenue" in body
    assert "net_profit" in body
    assert "gross_margin_pct" in body


@pytest.mark.asyncio
async def test_bad_category_rejected(client, auth):
    r = await client.post(
        "/api/v1/finance/expenses",
        json={"category": "invalid_cat", "amount": 100},
        headers=auth,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_enrich_adds_expenses(db):
    """enrich_all expenses ekler (idempotent)."""
    from app.services.demo_enricher import enrich_all

    r1 = await enrich_all(db)
    assert r1.get("expenses_created", 0) > 30  # 6 ay × ~6-13 gider
    # 2. çağrıda yeni gider yok
    r2 = await enrich_all(db)
    assert r2.get("expenses_created", 0) == 0
