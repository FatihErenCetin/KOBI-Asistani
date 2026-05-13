"""Günlük marketplace analizi — komşu trend'leri tarayıp öneri üretir.

Her gün 08:30'da çalışır. Tüm aktif admin'ler için (admin'in city/carrier'ına
göre) analiz yapar ve admin Telegram'a kısa özet atar.

Şu an scope tek-tenant: tek bir AdminUser (ilk aktif). Multi-tenant gelecekte
admin'ler tek tek dolaşılır.
"""

import logging

from sqlalchemy import select

from app.core.config import settings
from app.db.models import AdminUser
from app.db.session import SessionLocal
from app.services import marketplace_advisor

logger = logging.getLogger(__name__)


async def run_marketplace_analysis() -> int:
    """Marketplace advisor'ı çalıştır + admin Telegram özet bildirim gönder."""
    async with SessionLocal() as db:
        # Şu an scope: en eski aktif admin (tek tenant)
        res = await db.execute(
            select(AdminUser)
            .where(AdminUser.is_active.is_(True))
            .order_by(AdminUser.id.asc())
            .limit(1)
        )
        admin = res.scalar_one_or_none()

        recs = await marketplace_advisor.run_analysis(db, admin=admin)
        await db.commit()

        if not recs:
            logger.info("Marketplace cron: no new recommendations")
            return 0

        # Admin'e telegram özet (varsa)
        chat_id = admin.telegram_chat_id if admin else None
        if not chat_id and settings.ADMIN_TELEGRAM_ID:
            try:
                chat_id = int(settings.ADMIN_TELEGRAM_ID)
            except ValueError:
                chat_id = None

        if chat_id:
            top = recs[:3]
            body_lines = [
                f"🛒 Komşu trend bazlı {len(recs)} satınalma önerisi var:",
                "",
            ]
            for r in top:
                supplier_name = (
                    r.suggested_supplier.name if r.suggested_supplier else "-"
                )
                body_lines.append(
                    f"• {r.product_name} — {r.suggested_quantity:.0f} br "
                    f"({supplier_name}, %{int(r.confidence * 100)} güven)"
                )
            if len(recs) > 3:
                body_lines.append(f"  ...ve {len(recs) - 3} öneri daha")
            body_lines.append("")
            body_lines.append("Panel → Tedarikçi Pazarı → AI Önerileri")
            msg = "\n".join(body_lines)
            try:
                from app.integrations.telegram_client import telegram_client

                await telegram_client.send_message(chat_id, msg, parse_mode="")
                logger.info("Marketplace cron: admin notified, recs=%d", len(recs))
            except Exception:
                logger.exception("Marketplace cron: telegram notify failed")

        return len(recs)
