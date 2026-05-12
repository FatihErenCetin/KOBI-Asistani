import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import customers as customers_crud
from app.db.models import Customer

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Tum non-digit karakterleri at, basinda + olabilir."""
    digits = re.sub(r"\D", "", phone)
    return "+" + digits if digits else ""


async def resolve_by_telegram(
    db: AsyncSession, telegram_user_id: int
) -> Customer | None:
    return await customers_crud.get_by_telegram(db, telegram_user_id)


async def link_telegram_to_phone(
    db: AsyncSession,
    telegram_user_id: int,
    phone: str,
    *,
    fallback_name: str = "Musteri",
) -> Customer:
    """Telefon numarasiyla mevcut musteriyi bul veya yeni olustur."""
    norm = normalize_phone(phone)
    customer = await customers_crud.get_by_phone(db, norm)
    if customer is None:
        customer = await customers_crud.create(
            db, name=fallback_name, phone=norm, telegram_user_id=telegram_user_id
        )
    else:
        await customers_crud.link_telegram(db, customer, telegram_user_id)
    await db.commit()
    return customer
