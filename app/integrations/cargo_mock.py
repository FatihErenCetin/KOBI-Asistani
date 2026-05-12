import random
import string
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderStatus, Shipment, ShipmentStatus

LOCATIONS = [
    "Ankara Aktarma",
    "Istanbul Anadolu Subesi",
    "Istanbul Avrupa Subesi",
    "Izmir Dagitim",
    "Bursa Subesi",
    "Adana Aktarma",
    "Antalya Subesi",
]

STATE_ORDER = [
    ShipmentStatus.LABEL_CREATED,
    ShipmentStatus.PICKED_UP,
    ShipmentStatus.IN_TRANSIT,
    ShipmentStatus.OUT_FOR_DELIVERY,
    ShipmentStatus.DELIVERED,
]


def _generate_tracking_no() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TR{suffix}"


async def _existing_shipment_for_order(db: AsyncSession, order_id: int) -> Shipment | None:
    res = await db.execute(select(Shipment).where(Shipment.order_id == order_id))
    return res.scalar_one_or_none()


async def create_shipment(db: AsyncSession, order: Order) -> Shipment:
    """Order PREPARED -> SHIPPED gecisinde cagrilir."""
    existing = await _existing_shipment_for_order(db, order.id)
    if existing is not None:
        return existing
    shipment = Shipment(
        order_id=order.id,
        tracking_no=_generate_tracking_no(),
        carrier="MockKargo",
        status=ShipmentStatus.LABEL_CREATED,
        last_event_at=datetime.utcnow(),
        estimated_delivery=date.today() + timedelta(days=random.randint(1, 3)),
        current_location=random.choice(LOCATIONS),
    )
    db.add(shipment)
    await db.flush()
    return shipment


async def advance(db: AsyncSession, shipment: Shipment) -> Shipment:
    """Durumu bir adim ilerlet. DELIVERED ise no-op.

    Order'a lazy-loadla erismek async'te hata ureteceginden order'i id ile cekiyoruz.
    """
    try:
        idx = STATE_ORDER.index(shipment.status)
    except ValueError:
        idx = 0
    if idx < len(STATE_ORDER) - 1:
        shipment.status = STATE_ORDER[idx + 1]
        shipment.last_event_at = datetime.utcnow()
        if shipment.status in (ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY):
            shipment.current_location = random.choice(LOCATIONS)
        if shipment.status == ShipmentStatus.DELIVERED:
            shipment.current_location = "Teslim edildi"
            order = await db.get(Order, shipment.order_id)
            if order:
                order.status = OrderStatus.DELIVERED
        await db.flush()
    return shipment


def get_status_summary(shipment: Shipment) -> dict:
    return {
        "tracking_no": shipment.tracking_no,
        "carrier": shipment.carrier,
        "status": shipment.status.value,
        "location": shipment.current_location,
        "eta": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
        "last_event_at": shipment.last_event_at.isoformat(),
    }
