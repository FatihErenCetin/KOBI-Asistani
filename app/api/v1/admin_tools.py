"""Admin yardimci endpoint'leri — idempotent operasyonlar."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.services.demo_enricher import enrich_all

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.post("/enrich-demo-data", response_model=dict)
async def enrich_demo_data(db: AsyncSession = Depends(get_db)):
    """Prod-safe: mevcut veriye dokunmadan demo zenginlestirir.

    - Eksik depolari ekler (Sube, Soguk Hava, Arac).
    - Sadece Ana Depo'da stoğu olan urunleri MULTI_WAREHOUSE_SPLIT'e gore dagit.
    - LOT_CATALOG'taki SKT'li lot'lari (mevcut lot_number'lar disinda) ekle.

    Idempotent: birden fazla calistirilabilir.
    """
    return await enrich_all(db)
