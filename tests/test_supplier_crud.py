import pytest

from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import suppliers as suppliers_crud


@pytest.mark.asyncio
async def test_create_and_list_supplier(db):
    s = await suppliers_crud.create(db, name="Test Tedarikci", phone="+90555")
    assert s.id is not None
    rows = await suppliers_crud.list_all(db)
    assert any(r.id == s.id for r in rows)


@pytest.mark.asyncio
async def test_soft_delete_supplier_hides_from_default_list(db):
    s = await suppliers_crud.create(db, name="Gecici")
    await suppliers_crud.soft_delete(db, s)
    rows = await suppliers_crud.list_all(db)
    assert all(r.id != s.id for r in rows)
    rows_all = await suppliers_crud.list_all(db, include_inactive=True)
    assert any(r.id == s.id for r in rows_all)


@pytest.mark.asyncio
async def test_add_link_with_preferred_flips_existing(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    s1 = await suppliers_crud.create(db, name="A")
    s2 = await suppliers_crud.create(db, name="B")
    await ps_crud.add_link(db, product_id=p.id, supplier_id=s1.id, is_preferred=True)
    await ps_crud.add_link(db, product_id=p.id, supplier_id=s2.id, is_preferred=True)
    links = await ps_crud.list_for_product(db, p.id)
    preferred = [link for link in links if link.is_preferred]
    assert len(preferred) == 1
    assert preferred[0].supplier_id == s2.id


@pytest.mark.asyncio
async def test_update_link_records_purchase_timestamp(db):
    p = await products_crud.create(db, name="Bal", unit="kg", price=200, cost=120)
    s = await suppliers_crud.create(db, name="X")
    link = await ps_crud.add_link(db, product_id=p.id, supplier_id=s.id)
    assert link.last_purchase_at is None
    await ps_crud.update_link(db, link, last_unit_cost=110.0)
    assert link.last_purchase_at is not None
