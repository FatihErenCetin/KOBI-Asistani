from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import products as products_crud
from app.schemas.product import ProductOut, StockUpdate

router = APIRouter(
    prefix="/products", tags=["products"], dependencies=[Depends(require_admin)]
)


def _to_out(p) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        aliases=p.aliases,
        unit=p.unit,
        price=p.price,
        stock=p.stock,
        low_stock_threshold=p.low_stock_threshold,
        description=p.description,
        is_low=p.stock <= p.low_stock_threshold,
    )


@router.get("", response_model=list[ProductOut])
async def list_products(
    search: str | None = Query(default=None),
    low_stock_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    products = await products_crud.list_all(
        db, low_stock_only=low_stock_only, search=search
    )
    return [_to_out(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return _to_out(p)


@router.patch("/{product_id}/stock", response_model=ProductOut)
async def update_stock(
    product_id: int,
    payload: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    p = await products_crud.get_by_id(db, product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    await products_crud.set_stock(db, p, payload.stock)
    await db.commit()
    return _to_out(p)
