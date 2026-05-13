"""Sabah brifing job'i.

Her gun belirlenen saatte yoneticiye Telegram uzerinden
gunun operasyonel ozetini ve oncelikli aksiyonlari gonderir.
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.llm import run_agent_loop
from app.db.models import Order, OrderItem, OrderStatus, Product, Shipment, ShipmentStatus
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client

logger = logging.getLogger(__name__)


async def _gather_briefing_data() -> dict:
    """Gunun operasyonel verisini toplar."""
    now = datetime.utcnow()
    today = date.today()
    yesterday = today - timedelta(days=1)
    last_24h = now - timedelta(hours=24)
    last_48h = now - timedelta(hours=48)

    async with SessionLocal() as db:
        # Bugun teslim edilmesi gereken kargolar
        shipments_res = await db.execute(
            select(Shipment)
            .where(Shipment.estimated_delivery == today)
            .where(Shipment.status != ShipmentStatus.DELIVERED)
            .options(
                selectinload(Shipment.order).selectinload(Order.customer),
                selectinload(Shipment.order).selectinload(Order.items).selectinload(OrderItem.product),
            )
        )
        todays_shipments = list(shipments_res.scalars())

        # Bekleyen siparisler (pending + prepared)
        pending_res = await db.execute(
            select(Order)
            .where(Order.status.in_([OrderStatus.PENDING, OrderStatus.PREPARED]))
            .options(
                selectinload(Order.customer),
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .order_by(Order.promised_delivery.asc().nulls_last())
        )
        pending_orders = list(pending_res.scalars())

        # Bugun teslim sozu verilmis ama hazir olmayan acil siparisler
        urgent_res = await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status.in_([OrderStatus.PENDING, OrderStatus.PREPARED]),
                    Order.promised_delivery <= today,
                )
            )
        )
        urgent_count = urgent_res.scalar_one()

        # Dun ve onceki gun geliri
        rev_24h_res = await db.execute(
            select(func.coalesce(func.sum(Order.total), 0.0))
            .where(Order.created_at >= last_24h)
            .where(Order.status != OrderStatus.CANCELLED)
        )
        revenue_24h = float(rev_24h_res.scalar_one())

        rev_prev_res = await db.execute(
            select(func.coalesce(func.sum(Order.total), 0.0))
            .where(Order.created_at >= last_48h)
            .where(Order.created_at < last_24h)
            .where(Order.status != OrderStatus.CANCELLED)
        )
        revenue_prev = float(rev_prev_res.scalar_one())

        # Siparis sayilari
        orders_24h_res = await db.execute(
            select(func.count(Order.id)).where(Order.created_at >= last_24h)
        )
        orders_24h = int(orders_24h_res.scalar_one())

        # Dusuk stoklar
        low_stock_res = await db.execute(
            select(Product).where(Product.stock <= Product.low_stock_threshold)
        )
        low_stock = list(low_stock_res.scalars())

        # Hareketsiz kargolar (48h+)
        stale_threshold = now - timedelta(hours=48)
        stale_res = await db.execute(
            select(func.count(Shipment.id)).where(
                and_(
                    Shipment.status.in_([
                        ShipmentStatus.IN_TRANSIT,
                        ShipmentStatus.OUT_FOR_DELIVERY,
                    ]),
                    Shipment.last_event_at < stale_threshold,
                )
            )
        )
        stale_count = int(stale_res.scalar_one())

    # Veriyi ozetle
    shipment_summaries = [
        {
            "order_id": s.order_id,
            "customer": s.order.customer.name if s.order and s.order.customer else "?",
            "tracking": s.tracking_no,
            "carrier": s.carrier,
            "status": s.status.value,
            "location": s.current_location,
            "items": [i.product.name for i in s.order.items if i.product] if s.order else [],
        }
        for s in todays_shipments
    ]

    pending_summaries = [
        {
            "order_id": o.id,
            "customer": o.customer.name if o.customer else "?",
            "status": o.status.value,
            "total": o.total,
            "promised": o.promised_delivery.isoformat() if o.promised_delivery else None,
            "items": [i.product.name for i in o.items if i.product],
        }
        for o in pending_orders[:10]  # max 10
    ]

    low_stock_summaries = [
        {
            "name": p.name,
            "stock": p.stock,
            "threshold": p.low_stock_threshold,
            "unit": p.unit,
        }
        for p in low_stock
    ]

    revenue_change_pct = (
        ((revenue_24h - revenue_prev) / revenue_prev * 100) if revenue_prev > 0 else 0.0
    )

    return {
        "date": today.isoformat(),
        "revenue_24h": round(revenue_24h, 2),
        "revenue_prev_24h": round(revenue_prev, 2),
        "revenue_change_pct": round(revenue_change_pct, 1),
        "orders_24h": orders_24h,
        "pending_count": len(pending_orders),
        "urgent_count": urgent_count,
        "todays_shipments": shipment_summaries,
        "pending_orders": pending_summaries,
        "low_stock": low_stock_summaries,
        "stale_shipments_count": stale_count,
    }


BRIEFING_SYSTEM_PROMPT = """Sen bir KOBİ'nin operasyon asistanısın.
Yöneticiye her sabah kısa, net ve aksiyona yönelik bir brifing hazırlıyorsun.
Türkçe karakterleri tam kullan. Emoji kullanabilirsin (az, sadece vurgu için).
Format:
- Önce 2-3 cümle genel durum özeti
- Sonra öncelikli aksiyonlar listesi (en önemliden başla, max 5 madde)
- En sonda kısa bir motivasyon/kapanış cümlesi
Rakamları Türkçe formatla. Fazla detaya girme, yönetici zaten panelden bakabilir."""


async def _generate_briefing(data: dict) -> str:
    """LLM ile brifing metni uretir."""
    low_stock_str = (
        ", ".join(f"{p['name']} ({p['stock']} {p['unit']})" for p in data["low_stock"])
        if data["low_stock"] else "yok"
    )
    shipment_str = (
        ", ".join(f"#{s['order_id']} {s['customer']}" for s in data["todays_shipments"])
        if data["todays_shipments"] else "yok"
    )
    pending_urgent = [o for o in data["pending_orders"] if o["status"] == "pending"]

    user_prompt = f"""Tarih: {data['date']}

GELİR:
- Son 24 saat: {data['revenue_24h']} TL ({data['revenue_change_pct']:+.1f}% önceki güne göre)
- Sipariş sayısı: {data['orders_24h']}

SİPARİŞLER:
- Bekleyen/hazırlanacak: {data['pending_count']} sipariş
- Bugün teslim sözü verilmiş hazır olmayan (ACİL): {data['urgent_count']} sipariş
- Hazırlanmamış siparişler: {len(pending_urgent)} adet

KARGO:
- Bugün teslim edilecek: {len(data['todays_shipments'])} kargo ({shipment_str})
- 48 saatten uzun süredir hareketsiz kargo: {data['stale_shipments_count']} adet

STOK:
- Düşük stok uyarısı: {low_stock_str}

Bu verilere göre yöneticiye sabah brifingini hazırla."""

    result = await run_agent_loop(
        system_prompt=BRIEFING_SYSTEM_PROMPT,
        user_message=user_prompt,
        tools=[],
    )
    return (result.text or "").strip()


async def send_morning_briefing() -> None:
    """Ana job fonksiyonu - scheduler tarafindan cagrilir."""
    logger.info("Generating morning briefing")
    admin_id = settings.ADMIN_TELEGRAM_ID
    if not admin_id:
        logger.warning("ADMIN_TELEGRAM_ID not set, skipping morning briefing")
        return

    try:
        data = await _gather_briefing_data()
    except Exception:
        logger.exception("Failed to gather briefing data")
        return

    try:
        briefing_text = await _generate_briefing(data)
    except Exception:
        logger.exception("Failed to generate briefing text")
        return

    message = f"☀️ Günaydın! İşte bugünün özeti:\n\n{briefing_text}"

    try:
        await telegram_client.send_message(int(admin_id), message)
        logger.info("Morning briefing sent to admin %s", admin_id)
    except Exception:
        logger.exception("Failed to send morning briefing")
