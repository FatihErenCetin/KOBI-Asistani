from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import warehouses as warehouses_crud
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate

router = APIRouter(
    prefix="/warehouses", tags=["warehouses"], dependencies=[Depends(require_admin)]
)


def _to_out(w) -> WarehouseOut:
    return WarehouseOut(
        id=w.id,
        name=w.name,
        code=w.code,
        address=w.address,
        is_default=w.is_default,
        is_active=w.is_active,
        created_at=w.created_at,
    )


@router.get("", response_model=list[WarehouseOut])
async def list_warehouses(
    search: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    rows = await warehouses_crud.list_all(
        db, search=search, include_inactive=include_inactive
    )
    return [_to_out(w) for w in rows]


@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
async def create_warehouse(payload: WarehouseCreate, db: AsyncSession = Depends(get_db)):
    w = await warehouses_crud.create(db, **payload.model_dump())
    await db.commit()
    return _to_out(w)


@router.get("/{warehouse_id}", response_model=WarehouseOut)
async def get_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    w = await warehouses_crud.get_by_id(db, warehouse_id)
    if w is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    return _to_out(w)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
async def patch_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: AsyncSession = Depends(get_db),
):
    w = await warehouses_crud.get_by_id(db, warehouse_id)
    if w is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    await warehouses_crud.update(db, w, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return _to_out(w)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db)):
    w = await warehouses_crud.get_by_id(db, warehouse_id)
    if w is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Warehouse not found")
    try:
        await warehouses_crud.soft_delete(db, w)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    await db.commit()
