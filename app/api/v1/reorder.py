from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import reorder as reorder_crud

router = APIRouter(
    prefix="/reorder", tags=["reorder"], dependencies=[Depends(require_admin)]
)


@router.get("/suggestions", response_model=list[dict])
async def list_suggestions(db: AsyncSession = Depends(get_db)):
    """Stogu min_stock altinda olan urunler icin siparis onerileri."""
    return await reorder_crud.suggestions(db)
