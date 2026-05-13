"""Proaktif gecikme tespiti job'i.

Senaryo 1: promised_delivery gecmis, siparis hala shipped
Senaryo 2: kargo 2+ gundur hareketsiz (in_transit / out_for_delivery)
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Order, OrderItem, OrderStatus, Shipment, ShipmentStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

STALE_HOURS = 48  # Senaryo 2 esigi


async def detect_delays() -> dict:
    """Geciken/takili kargolari tespit eder, dict olarak doner."""
    now = datetime.utcnow()
    today = date.today()
    stale_threshold = now - timedelta(hours=STALE_HOURS)

    overdue: list[dict] = []   # Senaryo 1
    stale: list[dict] = []     # Senaryo 2

    async with SessionLocal() as db:
        result = await db.execute(
            select(Shipment)
            .where(
                Shipment.status.in_([
                    ShipmentStatus.PICKED_UP,
                    ShipmentStatus.IN_TRANSIT,
                    ShipmentStatus.OUT_FOR_DELIVERY,
                ])
            )
            .options(
                selectinload(Shipment.order).selectinload(Order.customer),
                selectinload(Shipment.order).selectinload(Order.items).selectinload(OrderItem.product),
            )
        )
        shipments = list(result.scalars())

    for s in shipments:
        order = s.order
        if order is None or order.status == OrderStatus.CANCELLED:
            continue

        customer = order.customer
        if customer is None or customer.telegram_user_id is None:
            continue

        item_names = [
            i.product.name for i in order.items if i.product
        ]

        base = {
            "order_id": order.id,
            "tracking_no": s.tracking_no,
            "carrier": s.carrier,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "telegram_user_id": customer.telegram_user_id,
            "current_location": s.current_location,
            "shipment_status": s.status.value,
            "promised_delivery": order.promised_delivery.isoformat() if order.promised_delivery else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "last_event_at": s.last_event_at.isoformat(),
            "items": item_names,
        }

        # Senaryo 1: sozlesilen tarih gecmis
        if order.promised_delivery and order.promised_delivery < today:
            days_late = (today - order.promised_delivery).days
            overdue.append({**base, "days_late": days_late})

        # Senaryo 2: son event cok eski
        elif s.last_event_at < stale_threshold:
            hours_stale = int((now - s.last_event_at).total_seconds() / 3600)
            stale.append({**base, "hours_stale": hours_stale})

    logger.info(
        "Delay detection: %d overdue, %d stale shipments found",
        len(overdue), len(stale)
    )
    return {"overdue": overdue, "stale": stale}
