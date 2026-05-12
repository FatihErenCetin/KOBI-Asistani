import logging
import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Shipment, ShipmentStatus
from app.db.session import SessionLocal
from app.integrations import cargo_mock

logger = logging.getLogger(__name__)


async def advance_active_shipments(sample_ratio: float = 0.3) -> int:
    """Aktif kargolarin bir kismini bir adim ilerlet (demo polish)."""
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
        for s in chosen:
            await cargo_mock.advance(db, s)
        await db.commit()
        logger.info("Cargo auto-advance: %d shipments advanced", len(chosen))
        return len(chosen)
