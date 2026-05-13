import logging
import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Shipment, ShipmentStatus
from app.db.session import SessionLocal
from app.integrations import cargo_mock
from app.services import shipment_notifier

logger = logging.getLogger(__name__)


async def advance_active_shipments(sample_ratio: float = 0.3) -> int:
    """Aktif kargolarin bir kismini bir adim ilerlet (demo polish).

    Status degisikligi olan her shipment icin musteriye Telegram bildirimi
    gonderilir (best-effort; bildirim hatasi ilerletmeyi etkilemez).
    """
    async with SessionLocal() as db:
        res = await db.execute(
            select(Shipment)
            .where(Shipment.status != ShipmentStatus.DELIVERED)
            .options(selectinload(Shipment.order))
        )
        actives = list(res.scalars())
        if not actives:
            return 0
        chosen = random.sample(actives, k=max(1, int(len(actives) * sample_ratio)))
        transitions: list[tuple[Shipment, ShipmentStatus]] = []
        for s in chosen:
            old = s.status
            await cargo_mock.advance(db, s)
            if s.status != old:
                transitions.append((s, s.status))
        await db.commit()

        for shipment, new_status in transitions:
            try:
                await shipment_notifier.notify_status_change(
                    db, shipment, new_status
                )
            except Exception:
                logger.exception(
                    "Notify failed (job): shipment=%s status=%s",
                    shipment.id, new_status.value,
                )

        logger.info("Cargo auto-advance: %d shipments advanced", len(chosen))
        return len(chosen)
