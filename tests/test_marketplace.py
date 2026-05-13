"""Marketplace modülü — endpoint + advisor smoke testleri."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import marketplace as mp_crud
from app.db.models import (
    NearbyShop,
    NearbyShopPurchase,
    Product,
    PurchaseOrderStatus,
    Supplier,
)
from app.main import app
from app.services import marketplace_advisor


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


async def _make_supplier(db, name="Test Tedarikci", **kwargs) -> Supplier:
    s = Supplier(
        name=name,
        category=kwargs.get("category", "Bal & Recel"),
        carrier=kwargs.get("carrier", "Yurtici Kargo"),
        city=kwargs.get("city", "Istanbul"),
        district=kwargs.get("district"),
        description=kwargs.get("description"),
        rating=kwargs.get("rating", 4.5),
        is_active=True,
    )
    db.add(s)
    await db.flush()
    return s


async def _make_product(db, name="Bal", cost=180, stock=5) -> Product:
    p = Product(name=name, unit="kg", price=280, cost=cost, stock=stock,
                low_stock_threshold=10)
    db.add(p)
    await db.flush()
    return p


@pytest.mark.asyncio
async def test_marketplace_suppliers_list_and_filters(client, db, auth):
    await _make_supplier(db, name="Bal A", category="Bal", carrier="Yurtici Kargo")
    await _make_supplier(db, name="Zeytin A", category="Zeytin", carrier="Aras Kargo")

    r = await client.get("/api/v1/marketplace/suppliers", headers=auth)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2

    r = await client.get(
        "/api/v1/marketplace/suppliers?category=Bal", headers=auth
    )
    assert all(s["category"] == "Bal" for s in r.json())

    r = await client.get(
        "/api/v1/marketplace/suppliers?carrier=Aras Kargo", headers=auth
    )
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_purchase_order_create_and_receive_updates_stock(client, db, auth):
    sup = await _make_supplier(db)
    prod = await _make_product(db, stock=5)
    initial_stock = prod.stock

    r = await client.post(
        "/api/v1/marketplace/purchase-orders",
        json={
            "supplier_id": sup.id,
            "items": [{"product_id": prod.id, "quantity": 8, "unit_cost": 180}],
            "notes": "Test PO",
        },
        headers=auth,
    )
    assert r.status_code == 201
    po = r.json()
    assert po["status"] == "draft"
    assert po["total_cost"] == 1440  # 8 * 180

    # Receive geçişi → stok artmalı
    r = await client.patch(
        f"/api/v1/marketplace/purchase-orders/{po['id']}/status",
        json={"status": "received"},
        headers=auth,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "received"
    assert r.json()["received_at"] is not None

    # Product stok güncellendi mi?
    await db.refresh(prod)
    assert prod.stock == initial_stock + 8


@pytest.mark.asyncio
async def test_unknown_supplier_400(client, auth):
    r = await client.post(
        "/api/v1/marketplace/purchase-orders",
        json={
            "supplier_id": 99999,
            "items": [{"product_id": 1, "quantity": 1, "unit_cost": 1}],
        },
        headers=auth,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_nearby_signals_and_advisor(client, db, auth):
    # Setup: 3 yakın komşu Istanbul'da, hepsi bal alıyor
    shops = []
    for i, name in enumerate(["Shop A", "Shop B", "Shop C"]):
        s = NearbyShop(
            name=name, city="Istanbul", district="Kadikoy",
            preferred_carrier="Yurtici Kargo", is_active=True,
            distance_km=float(i + 1),
        )
        db.add(s)
        await db.flush()
        shops.append(s)

    sup = await _make_supplier(db, name="Bal Sup", category="Bal")
    # Her komşu son 1 hafta içinde bal aldı
    for shop in shops:
        db.add(
            NearbyShopPurchase(
                shop_id=shop.id,
                supplier_id=sup.id,
                product_name="Bal",
                product_category="Bal",
                quantity=10,
                unit_cost=185,
                carrier="Yurtici Kargo",
                purchased_at=datetime.utcnow() - timedelta(days=3),
            )
        )
    await db.flush()

    # Bizim katalogda Bal var, stok düşük
    prod = await _make_product(db, name="Bal", stock=2)

    # Signal endpoint çalışıyor mu?
    r = await client.get(
        "/api/v1/marketplace/nearby-signals?city=Istanbul&since_days=14",
        headers=auth,
    )
    assert r.status_code == 200
    signals = r.json()
    assert any(s["product_name"] == "Bal" and s["shop_count"] == 3 for s in signals)

    # Advisor çalıştır
    recs = await marketplace_advisor.run_analysis(
        db, admin=None, since_days=14, min_signal_count=2, max_recommendations=5
    )
    await db.commit()
    assert len(recs) >= 1
    bal_rec = next((r for r in recs if r.product_name == "Bal"), None)
    assert bal_rec is not None
    assert bal_rec.suggested_supplier_id == sup.id
    assert bal_rec.product_id == prod.id
    assert bal_rec.nearby_signal_count == 3


@pytest.mark.asyncio
async def test_recommendation_apply_creates_po(client, db, auth):
    """AI öneri sipariş olarak uygulandığında recommendation status=applied."""
    sup = await _make_supplier(db)
    prod = await _make_product(db)

    rec = await mp_crud.create_recommendation(
        db,
        product_name=prod.name,
        product_id=prod.id,
        suggested_supplier_id=sup.id,
        suggested_quantity=10,
        estimated_unit_cost=180,
        confidence=0.8,
        reasoning="Test öneri",
        nearby_signal_count=3,
    )
    await db.commit()

    r = await client.post(
        "/api/v1/marketplace/purchase-orders",
        json={
            "supplier_id": sup.id,
            "items": [{"product_id": prod.id, "quantity": 10, "unit_cost": 180}],
            "recommendation_id": rec.id,
        },
        headers=auth,
    )
    assert r.status_code == 201
    po = r.json()
    assert po["ai_suggested"] is True
    assert po["suggestion_reason"] == "Test öneri"

    # Rec status applied olmalı
    await db.refresh(rec)
    assert rec.status == "applied"


@pytest.mark.asyncio
async def test_marketplace_requires_auth(client):
    r = await client.get("/api/v1/marketplace/suppliers")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_advisor_fallback_without_llm(db):
    """Gemini yokken deterministik fallback üretim üretmeli."""
    shops = []
    for i in range(2):
        s = NearbyShop(
            name=f"S{i}", city="Istanbul", preferred_carrier="X",
            is_active=True, distance_km=1.0,
        )
        db.add(s)
        await db.flush()
        shops.append(s)
    for shop in shops:
        db.add(
            NearbyShopPurchase(
                shop_id=shop.id,
                supplier_id=None,
                product_name="YeniUrun",
                product_category="Test",
                quantity=10,
                unit_cost=50,
                carrier="X",
                purchased_at=datetime.utcnow() - timedelta(days=2),
            )
        )
    await db.flush()

    from unittest.mock import patch
    with patch.object(
        marketplace_advisor.settings, "GEMINI_API_KEY", ""
    ), patch.object(marketplace_advisor.settings, "GEMINI_API_KEYS", ""):
        recs = await marketplace_advisor.run_analysis(
            db, admin=None, since_days=14, min_signal_count=2
        )
    assert len(recs) >= 1
    # Fallback gerekçesinde "komşu" ya da "KOBİ" geçmeli
    assert "KOBİ" in recs[0].reasoning or "komşu" in recs[0].reasoning


@pytest.mark.asyncio
async def test_purchase_order_status_enum_values():
    """5 status değeri tanımlı olmalı."""
    values = {s.value for s in PurchaseOrderStatus}
    assert values == {"draft", "sent", "confirmed", "received", "cancelled"}
