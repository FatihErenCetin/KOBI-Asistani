from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import suppliers as suppliers_crud
from app.schemas.supplier import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(
    prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_admin)]
)


async def _to_out(db: AsyncSession, s) -> SupplierOut:
    n = await suppliers_crud.count_linked_products(db, s.id)
    return SupplierOut(
        id=s.id,
        name=s.name,
        contact_name=s.contact_name,
        phone=s.phone,
        email=s.email,
        address=s.address,
        notes=s.notes,
        is_active=s.is_active,
        created_at=s.created_at,
        linked_product_count=n,
    )


@router.get("", response_model=list[SupplierOut])
async def list_suppliers(
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    rows = await suppliers_crud.list_all(
        db, search=search, include_inactive=include_inactive
    )
    return [await _to_out(db, s) for s in rows]


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
async def create_supplier(payload: SupplierCreate, db: AsyncSession = Depends(get_db)):
    s = await suppliers_crud.create(db, **payload.model_dump())
    await db.commit()
    return await _to_out(db, s)


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    s = await suppliers_crud.get_by_id(db, supplier_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    return await _to_out(db, s)


@router.patch("/{supplier_id}", response_model=SupplierOut)
async def patch_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
):
    s = await suppliers_crud.get_by_id(db, supplier_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    await suppliers_crud.update(db, s, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return await _to_out(db, s)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db)):
    s = await suppliers_crud.get_by_id(db, supplier_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Supplier not found")
    await suppliers_crud.soft_delete(db, s)
    await db.commit()
