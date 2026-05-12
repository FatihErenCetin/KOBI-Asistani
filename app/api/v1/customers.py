from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import customers as customers_crud
from app.db.crud import orders as orders_crud
from app.db.models import Customer
from app.schemas.customer import CustomerOut
from app.schemas.order import (
    CustomerSummary,
    OrderItemOut,
    OrderOut,
    ShipmentOut,
)

router = APIRouter(
    prefix="/customers", tags=["customers"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[CustomerOut])
async def list_customers(
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    if search:
        results = await customers_crud.search(db, search)
    else:
        res = await db.execute(select(Customer).order_by(Customer.name).limit(200))
        results = list(res.scalars())
    return [
        CustomerOut(
            id=c.id,
            name=c.name,
            phone=c.phone,
            telegram_user_id=c.telegram_user_id,
            created_at=c.created_at,
        )
        for c in results
    ]


@router.get("/{customer_id}/orders", response_model=list[OrderOut])
async def list_customer_orders(
    customer_id: int, db: AsyncSession = Depends(get_db)
):
    c = await customers_crud.get_by_id(db, customer_id)
    if c is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")
    orders = await orders_crud.list_orders(db, customer_id=customer_id, limit=100)
    return [
        OrderOut(
            id=o.id,
            status=o.status.value,
            total=o.total,
            created_at=o.created_at,
            promised_delivery=o.promised_delivery,
            note=o.note,
            customer=CustomerSummary(
                id=o.customer.id, name=o.customer.name, phone=o.customer.phone
            ),
            items=[
                OrderItemOut(
                    id=i.id,
                    product_id=i.product_id,
                    product_name=i.product.name if i.product else "?",
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                )
                for i in o.items
            ],
            shipment=(
                ShipmentOut(
                    tracking_no=o.shipment.tracking_no,
                    carrier=o.shipment.carrier,
                    status=o.shipment.status.value,
                    current_location=o.shipment.current_location,
                    estimated_delivery=o.shipment.estimated_delivery,
                )
                if o.shipment
                else None
            ),
        )
        for o in orders
    ]
