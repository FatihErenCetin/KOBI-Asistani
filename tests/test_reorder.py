"""M8: Reorder suggestions."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import reorder as reorder_crud
from app.db.crud import suppliers as suppliers_crud
from app.db.models import StockMovementReason
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
async def test_low_stock_appears_in_suggestions(db):
    p = await products_crud.create(
        db, name="Bal", unit="kg", price=100, cost=50,
        low_stock_threshold=10, max_stock=50,
    )
    await products_crud.adjust_stock(db, p, 3, reason=StockMovementReason.INITIAL)
    s = await suppliers_crud.create(db, name="Bal Tedarikçisi")
    await ps_crud.add_link(
        db, product_id=p.id, supplier_id=s.id,
        last_unit_cost=45, lead_time_days=3, is_preferred=True,
    )

    rows = await reorder_crud.suggestions(db)
    target = next((r for r in rows if r["product_name"] == "Bal"), None)
    assert target is not None
    assert target["suggested_order_qty"] == 47  # 50 - 3
    assert target["supplier_name"] == "Bal Tedarikçisi"
    assert target["lead_time_days"] == 3


@pytest.mark.asyncio
async def test_full_stock_not_in_suggestions(db):
    p = await products_crud.create(
        db, name="Bol", unit="kg", price=10, cost=5, low_stock_threshold=5,
    )
    await products_crud.adjust_stock(db, p, 100, reason=StockMovementReason.INITIAL)
    rows = await reorder_crud.suggestions(db)
    assert all(r["product_name"] != "Bol" for r in rows)


@pytest.mark.asyncio
async def test_no_max_stock_uses_default_qty(db):
    p = await products_crud.create(
        db, name="X", unit="kg", price=10, cost=5, low_stock_threshold=10,
    )
    rows = await reorder_crud.suggestions(db)
    target = next((r for r in rows if r["product_name"] == "X"), None)
    assert target is not None
    # max_stock yok → min*2 = 20
    assert target["suggested_order_qty"] == 20


@pytest.mark.asyncio
async def test_endpoint(client, auth, db):
    p = await products_crud.create(
        db, name="Bal", unit="kg", price=100, cost=50, low_stock_threshold=10,
    )
    await db.commit()
    r = await client.get("/api/v1/reorder/suggestions", headers=auth)
    assert r.status_code == 200
    assert any(row["product_name"] == "Bal" for row in r.json())
