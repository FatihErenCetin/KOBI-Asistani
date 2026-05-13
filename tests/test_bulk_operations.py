"""M5: CSV import/export + bulk price update + barkod arama."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.db.crud import price_history as ph_crud
from app.db.crud import products as products_crud
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
async def test_export_csv(client, auth, db):
    await products_crud.create(db, name="ExportProd", unit="kg", price=10, cost=5)
    await db.commit()
    r = await client.get("/api/v1/products/export.csv", headers=auth)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    body = r.text
    assert "id,name,unit" in body
    assert "ExportProd" in body


@pytest.mark.asyncio
async def test_import_csv_creates_and_updates(client, auth, db):
    # Mevcut bir ürün oluştur
    existing = await products_crud.create(
        db, name="MevcutProd", unit="kg", price=50, cost=25
    )
    await db.commit()

    csv_body = (
        "name,unit,price,cost,stock\n"
        "MevcutProd,kg,60,30,5\n"  # update
        "YeniProd,lt,100,60,10\n"  # create
        ",kg,99,50,1\n"  # skipped (name empty)
    )

    r = await client.post(
        "/api/v1/products/import.csv",
        files={"file": ("p.csv", csv_body, "text/csv")},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 1
    assert body["updated"] == 1
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["row"] == 4

    # Mevcut ürün artık 60 TL
    await db.refresh(existing)
    assert existing.price == 60


@pytest.mark.asyncio
async def test_bulk_price_percent_increase(client, auth, db):
    p1 = await products_crud.create(
        db, name="Bal1", unit="kg", price=100, cost=50, category="Gida"
    )
    p2 = await products_crud.create(
        db, name="Bal2", unit="kg", price=200, cost=100, category="Gida"
    )
    await products_crud.create(
        db, name="Sabun", unit="adet", price=20, cost=10, category="Temizlik"
    )
    await db.commit()

    r = await client.post(
        "/api/v1/products/bulk-price",
        json={
            "category": "Gida",
            "operation": "percent_increase",
            "value": 10,
            "target": "price",
            "reason": "Sezon zammı",
        },
        headers=auth,
    )
    assert r.status_code == 200
    assert r.json()["updated"] == 2

    await db.refresh(p1)
    await db.refresh(p2)
    assert p1.price == 110
    assert p2.price == 220

    # History'de "Sezon zammı" reason'u var
    rows = await ph_crud.list_for_product(db, p1.id)
    assert any(r.reason == "Sezon zammı" for r in rows)


@pytest.mark.asyncio
async def test_barcode_search(client, auth, db):
    await products_crud.create(
        db, name="ProdA", unit="kg", price=10, cost=5, barcode="1234567"
    )
    await products_crud.create(
        db, name="ProdB", unit="kg", price=10, cost=5, barcode="9999999"
    )
    await db.commit()

    r = await client.get("/api/v1/products?search=1234567", headers=auth)
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert "ProdA" in names
    assert "ProdB" not in names


@pytest.mark.asyncio
async def test_bulk_price_invalid_operation_rejected(client, auth):
    r = await client.post(
        "/api/v1/products/bulk-price",
        json={
            "operation": "invalid_op",
            "value": 5,
            "target": "price",
            "reason": "test",
        },
        headers=auth,
    )
    assert r.status_code == 400
