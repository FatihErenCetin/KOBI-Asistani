"""M3: AI panel tool'lari icin bulk analytics helper'lari."""

import pytest

from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.crud import product_analytics as analytics
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import suppliers as suppliers_crud
from app.db.models import StockMovementReason


@pytest.mark.asyncio
async def test_low_margin_products(db):
    # %50 marj
    await products_crud.create(db, name="HighMargin", unit="kg", price=100, cost=50)
    # %10 marj
    await products_crud.create(db, name="LowMargin", unit="kg", price=100, cost=90)
    # cost=0 → margin hesaplanmaz, listede yok
    await products_crud.create(db, name="NoCost", unit="kg", price=100, cost=0)

    rows = await analytics.low_margin_products(db, margin_threshold=20)
    names = [r["name"] for r in rows]
    assert "LowMargin" in names
    assert "HighMargin" not in names
    assert "NoCost" not in names


@pytest.mark.asyncio
async def test_low_margin_sorted_ascending(db):
    await products_crud.create(db, name="A", unit="kg", price=100, cost=90)  # 10
    await products_crud.create(db, name="B", unit="kg", price=100, cost=85)  # 15
    rows = await analytics.low_margin_products(db, margin_threshold=20)
    assert rows[0]["margin_pct"] <= rows[-1]["margin_pct"]


@pytest.mark.asyncio
async def test_fast_depleting_products(db):
    # Stok 10, günde 2 satılıyor → 5 gün dayanır → fast_depleting (max_days=7)
    p = await products_crud.create(db, name="FastP", unit="kg", price=10, cost=5)
    await products_crud.adjust_stock(db, p, 10, reason=StockMovementReason.INITIAL)
    c = await customers_crud.create(db, name="X")
    # 30 günlük velocity için son 30 günde 60 birim sat → günlük 2
    from datetime import datetime, timedelta
    from app.db.models import StockMovement
    for i in range(30):
        sm = StockMovement(
            product_id=p.id, delta=-2, reason=StockMovementReason.SALE,
            balance_after=10, created_at=datetime.utcnow() - timedelta(days=i),
        )
        db.add(sm)
    await db.flush()

    rows = await analytics.fast_depleting_products(db, max_days=7)
    assert any(r["name"] == "FastP" for r in rows)


@pytest.mark.asyncio
async def test_supplier_lead_time_stats(db):
    s = await suppliers_crud.create(db, name="LeadTest")
    p1 = await products_crud.create(db, name="P1", unit="kg", price=10, cost=5)
    p2 = await products_crud.create(db, name="P2", unit="kg", price=10, cost=5)
    await ps_crud.add_link(db, product_id=p1.id, supplier_id=s.id, lead_time_days=3)
    await ps_crud.add_link(db, product_id=p2.id, supplier_id=s.id, lead_time_days=7)

    rows = await analytics.supplier_lead_time_stats(db)
    target = next(r for r in rows if r["supplier_name"] == "LeadTest")
    assert target["avg_lead_time_days"] == 5.0
    assert target["linked_product_count"] == 2


@pytest.mark.asyncio
async def test_category_stock_overview(db):
    await products_crud.create(
        db, name="A", unit="kg", price=10, cost=5, category="Gida"
    )
    await products_crud.create(
        db, name="B", unit="kg", price=10, cost=5, category="Gida"
    )
    await products_crud.create(
        db, name="C", unit="kg", price=10, cost=5, category="Temizlik"
    )

    rows = await analytics.category_stock_overview(db)
    gida = next(r for r in rows if r["category"] == "Gida")
    assert gida["product_count"] == 2
