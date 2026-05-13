"""Sabah brifingi — APScheduler ile 09:00'da admin telegram chat'lerine push."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.crud import complaints as complaints_crud
from app.db.crud import orders as orders_crud
from app.db.crud import reorder as reorder_crud
from app.db.crud import stock_lots as lots_crud
from app.db.models import AdminUser
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client

logger = logging.getLogger(__name__)


def _fmt_tr_amount(amount: float) -> str:
    return (
        f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        + " TL"
    )


async def build_briefing_text(db) -> str:
    """Brifing icerigi: dun gelen siparis, kritik reorder, SKT yaklasan, acik sikayet."""
    from app.db.models import OrderStatus

    # Son 24 saat siparişleri
    since = datetime.utcnow() - timedelta(hours=24)
    revenue = await orders_crud.revenue_since(db, since)
    pending = await orders_crud.count_by_status(db, OrderStatus.PENDING)

    # Reorder — sadece kritik (urgency=critical)
    suggestions = await reorder_crud.suggestions(db)
    critical = [s for s in suggestions if s.get("urgency") == "critical"]

    # SKT yaklaşan
    expiring = await lots_crud.expiring_soon(db, within_days=7)

    # Açık şikayetler
    open_complaints = await complaints_crud.list_open(db, limit=5)

    lines = ["📅 *Günaydın!* İşte bugünün özeti:", ""]
    lines.append(f"💰 *Son 24 saat:* {_fmt_tr_amount(revenue)} ciro, {pending} bekleyen sipariş")
    if critical:
        lines.append("")
        lines.append(f"🚨 *Acil sipariş ({len(critical)}):*")
        for s in critical[:5]:
            lines.append(
                f"  • {s['product_name']}: {s['current_stock']} {s['unit']} "
                f"kaldı, {s['suggested_order_qty']} {s['unit']} sipariş öneri"
            )
    if expiring:
        lines.append("")
        lines.append(f"⏳ *SKT 7 gün içinde ({len(expiring)}):*")
        for lot in expiring[:5]:
            days = (lot.expiry_date - datetime.utcnow().date()).days
            lines.append(
                f"  • {lot.product.name} (lot {lot.lot_number}): {days} gün"
            )
    if open_complaints:
        lines.append("")
        lines.append(f"⚠️ *Açık şikayet ({len(open_complaints)}):*")
        for c in open_complaints[:3]:
            lines.append(f"  • Risk %{int(c.risk_score * 100)}: \"{c.message_text[:60]}…\"")

    lines.append("")
    lines.append("İyi çalışmalar 💪")
    return "\n".join(lines)


async def send_briefings():
    """APScheduler job: tum opt-in admin'lere brifing gonder."""
    try:
        async with SessionLocal() as db:
            res = await db.execute(
                select(AdminUser).where(
                    AdminUser.is_active.is_(True),
                    AdminUser.briefing_enabled.is_(True),
                    AdminUser.telegram_chat_id.is_not(None),
                )
            )
            admins = list(res.scalars())
            if not admins:
                logger.info("Briefing: opt-in admin yok, gonderim atlandi")
                return
            text = await build_briefing_text(db)
        # Send (DB session disinda)
        for admin in admins:
            try:
                await telegram_client.send_message(
                    admin.telegram_chat_id, text, parse_mode="Markdown"
                )
                logger.info("Briefing sent to admin %s (chat %s)", admin.email, admin.telegram_chat_id)
            except Exception:
                logger.exception("Briefing send failed for %s", admin.email)
    except Exception:
        logger.exception("Briefing job failed")
