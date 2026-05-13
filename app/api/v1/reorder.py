from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_optional, get_db, require_admin
from app.db.crud import product_suppliers as ps_crud
from app.db.crud import products as products_crud
from app.db.crud import reorder as reorder_crud
from app.db.crud import suppliers as suppliers_crud
from app.db.models import AdminUser
from app.services.mail_template import draft_reorder_mail

router = APIRouter(
    prefix="/reorder", tags=["reorder"], dependencies=[Depends(require_admin)]
)


class DraftMailRequest(BaseModel):
    product_id: int
    order_qty: float
    supplier_id: int | None = None  # None ise birincil tedarikci


@router.get("/suggestions", response_model=list[dict])
async def list_suggestions(db: AsyncSession = Depends(get_db)):
    """Stogu min_stock altinda olan urunler icin siparis onerileri."""
    return await reorder_crud.suggestions(db)


@router.post("/draft-mail", response_model=dict)
async def draft_mail(
    payload: DraftMailRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser | None = Depends(get_current_admin_optional),
):
    """Tedarikciye gonderilecek mail/SMS taslagi olustur (sadece text)."""
    p = await products_crud.get_by_id(db, payload.product_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    # Tedarikci sec
    link = None
    if payload.supplier_id is not None:
        link = await ps_crud.get_link(db, payload.product_id, payload.supplier_id)
    if link is None:
        # Birincil tedarikci fallback
        links = await ps_crud.list_for_product(db, payload.product_id)
        link = next((l for l in links if l.is_preferred), None) or (
            links[0] if links else None
        )

    if link is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Bu ürüne bağlı tedarikçi yok. Önce ürün detayından bağlayın.",
        )

    supplier = await suppliers_crud.get_by_id(db, link.supplier_id)
    admin_name = current_admin.name if current_admin else "İşletme"

    draft = draft_reorder_mail(
        supplier_name=supplier.name if supplier else "Tedarikçi",
        product_name=p.name,
        order_qty=payload.order_qty,
        unit=p.unit,
        last_unit_cost=link.last_unit_cost,
        lead_time_days=link.lead_time_days,
        admin_name=admin_name,
    )
    return {
        "subject": draft["subject"],
        "body": draft["body"],
        "supplier_email": supplier.email if supplier else None,
        "supplier_phone": supplier.phone if supplier else None,
    }
