from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.models import OrderStatus, ShipmentStatus
from app.integrations import cargo_mock
from app.services import shipment_notifier
from app.schemas.order import (
    CustomerSummary,
    OrderCreate,
    OrderItemOut,
    OrderOut,
    OrderStatusUpdate,
    ShipmentOut,
)

router = APIRouter(
    prefix="/orders", tags=["orders"], dependencies=[Depends(require_admin)]
)


def _to_out(order) -> OrderOut:
    return OrderOut(
        id=order.id,
        status=order.status.value,
        total=order.total,
        created_at=order.created_at,
        promised_delivery=order.promised_delivery,
        note=order.note,
        customer=CustomerSummary(
            id=order.customer.id,
            name=order.customer.name,
            phone=order.customer.phone,
        ),
        items=[
            OrderItemOut(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "?",
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
            for item in order.items
        ],
        shipment=(
            ShipmentOut(
                tracking_no=order.shipment.tracking_no,
                carrier=order.shipment.carrier,
                status=order.shipment.status.value,
                current_location=order.shipment.current_location,
                estimated_delivery=order.shipment.estimated_delivery,
            )
            if order.shipment
            else None
        ),
    )


@router.get("", response_model=list[OrderOut])
async def list_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    since: datetime | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    limit: int = Query(default=20, le=200),
    db: AsyncSession = Depends(get_db),
):
    status_enum = OrderStatus(status_filter) if status_filter else None
    orders = await orders_crud.list_orders(
        db, status=status_enum, since=since, customer_id=customer_id, limit=limit
    )
    return [_to_out(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await orders_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return _to_out(order)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    items = []
    for it in payload.items:
        p = await products_crud.get_by_id(db, int(it["product_id"]))
        if p is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Product {it['product_id']} missing"
            )
        items.append((p, float(it["quantity"])))
    order = await orders_crud.create_order(
        db, customer_id=payload.customer_id, items=items, note=payload.note
    )
    await db.commit()
    refreshed = await orders_crud.get_by_id(db, order.id)
    return _to_out(refreshed)


@router.patch("/{order_id}/status", response_model=OrderOut)
async def patch_status(
    order_id: int, payload: OrderStatusUpdate, db: AsyncSession = Depends(get_db)
):
    order = await orders_crud.get_by_id(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    try:
        new_status = OrderStatus(payload.status)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    old_status = order.status
    order.status = new_status
    shipment_to_notify = None
    if (
        old_status != OrderStatus.SHIPPED
        and new_status == OrderStatus.SHIPPED
        and not order.shipment
    ):
        shipment = await cargo_mock.create_shipment(db, order)
        shipment.status = ShipmentStatus.PICKED_UP
        shipment_to_notify = shipment
    await db.commit()
    if shipment_to_notify is not None:
        await shipment_notifier.notify_status_change(
            db, shipment_to_notify, ShipmentStatus.PICKED_UP
        )
    refreshed = await orders_crud.get_by_id(db, order.id)
    return _to_out(refreshed)
