"""Expiry advisor agent — yaklasan SKT'li lot'lar icin AI oneri uretici."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.crud import stock_balances as sb_crud
from app.db.crud import stock_lots as lots_crud
from app.db.models import (
    LotAction,
    LotActionStatus,
    LotActionType,
    StockMovementReason,
)
from app.main import app
from app.services import expiry_advisor
from sqlalchemy import select


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
async def test_fallback_actions_critical(db):
    """3 gün veya altı kalan lot için fallback acil indirim + bildirim önerir."""
    p = await products_crud.create(db, name="Bal", unit="kg", price=100, cost=50)
    await products_crud.adjust_stock(db, p, 20, reason=StockMovementReason.INITIAL)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="CRIT-01",
        quantity=20,
        expiry_date=date.today() + timedelta(days=2),
    )

    # LLM kapalı senaryo
    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        actions = await expiry_advisor.analyze_lot(db, lot)

    assert len(actions) >= 1
    types = {a.action_type for a in actions}
    assert LotActionType.DISCOUNT in types
    discount = next(a for a in actions if a.action_type == LotActionType.DISCOUNT)
    assert discount.suggested_discount_pct is not None
    assert discount.suggested_discount_pct >= 30
    assert discount.priority == 1


@pytest.mark.asyncio
async def test_fallback_waste_for_expired(db):
    """SKT'si geçmiş lot için fire önerisi."""
    p = await products_crud.create(db, name="X", unit="kg", price=10, cost=5)
    await products_crud.adjust_stock(db, p, 5, reason=StockMovementReason.INITIAL)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="EXPIRED",
        quantity=5,
        expiry_date=date.today() - timedelta(days=2),
    )

    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        actions = await expiry_advisor.analyze_lot(db, lot)

    types = {a.action_type for a in actions}
    assert LotActionType.WASTE in types


@pytest.mark.asyncio
async def test_fallback_delay_reorder_when_natural_consumption_too_slow(db):
    """5 gün SKT + 30 birim stok + günde 1 satış → tüketilemez, indirim + delay reorder."""
    p = await products_crud.create(db, name="Yavas", unit="kg", price=10, cost=5)
    await products_crud.adjust_stock(db, p, 30, reason=StockMovementReason.INITIAL)
    default = await sb_crud.get_default_warehouse(db)
    # Sat 5 birim son 30 günde → günde 0.17, 30 birim ~180 gün
    c = await customers_crud.create(db, name="x")
    for _ in range(5):
        await orders_crud.create_order(db, customer_id=c.id, items=[(p, 1)])

    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="SLOW",
        quantity=25,
        expiry_date=date.today() + timedelta(days=5),
    )

    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        actions = await expiry_advisor.analyze_lot(db, lot)

    types = {a.action_type for a in actions}
    assert LotActionType.DELAY_REORDER in types or LotActionType.DISCOUNT in types


@pytest.mark.asyncio
async def test_idempotent_skip(db):
    """Pending action varken yeniden analiz atlanır."""
    p = await products_crud.create(db, name="X", unit="kg", price=10, cost=5)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="DUP",
        quantity=10,
        expiry_date=date.today() + timedelta(days=4),
    )

    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        first = await expiry_advisor.analyze_lot(db, lot)
        second = await expiry_advisor.analyze_lot(db, lot)

    assert len(first) >= 1
    assert len(second) == 0  # pending varken atlandı


@pytest.mark.asyncio
async def test_force_bypasses_idempotent(db):
    p = await products_crud.create(db, name="X", unit="kg", price=10, cost=5)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="FORCE",
        quantity=10,
        expiry_date=date.today() + timedelta(days=4),
    )

    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        await expiry_advisor.analyze_lot(db, lot)
        forced = await expiry_advisor.analyze_lot(db, lot, force=True)

    assert len(forced) >= 1  # force ile yeni öneri eklenebildi


@pytest.mark.asyncio
async def test_llm_parsing(db):
    """LLM JSON döndürdüğünde parse edilebiliyor."""
    p = await products_crud.create(db, name="Y", unit="kg", price=10, cost=5)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="LLM",
        quantity=15,
        expiry_date=date.today() + timedelta(days=5),
    )
    fake_actions = [
        {
            "action_type": "discount",
            "subject": "%25 indirim önerisi",
            "description": "5 gün SKT kaldı, hızlı tüketim için indirim öner.",
            "suggested_discount_pct": 25,
            "priority": 1,
        }
    ]
    with patch.object(
        expiry_advisor,
        "_llm_propose_actions",
        new=AsyncMock(return_value=fake_actions),
    ):
        actions = await expiry_advisor.analyze_lot(db, lot)

    assert len(actions) == 1
    assert actions[0].action_type == LotActionType.DISCOUNT
    assert actions[0].suggested_discount_pct == 25
    assert "indirim" in actions[0].subject.lower()


@pytest.mark.asyncio
async def test_analyze_all_expiring_endpoint(client, auth, db):
    p = await products_crud.create(db, name="Z", unit="kg", price=10, cost=5)
    await products_crud.adjust_stock(db, p, 10, reason=StockMovementReason.INITIAL)
    default = await sb_crud.get_default_warehouse(db)
    await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="EP-01",
        quantity=10,
        expiry_date=date.today() + timedelta(days=5),
    )
    await db.commit()

    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        r = await client.post(
            "/api/v1/lot-actions/analyze?within_days=14", headers=auth
        )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lots_analyzed"] >= 1
    assert body["actions_created"] >= 1


@pytest.mark.asyncio
async def test_apply_action_endpoint(client, auth, db):
    p = await products_crud.create(db, name="A", unit="kg", price=10, cost=5)
    default = await sb_crud.get_default_warehouse(db)
    lot = await lots_crud.create(
        db,
        product_id=p.id,
        warehouse_id=default.id,
        lot_number="AP-01",
        quantity=5,
        expiry_date=date.today() + timedelta(days=4),
    )
    with patch.object(
        expiry_advisor, "_llm_propose_actions", new=AsyncMock(return_value=None)
    ):
        actions = await expiry_advisor.analyze_lot(db, lot)
    await db.commit()
    action_id = actions[0].id

    r = await client.post(f"/api/v1/lot-actions/{action_id}/apply", headers=auth)
    assert r.status_code == 200
    assert r.json()["status"] == "applied"
    assert r.json()["applied_at"] is not None
