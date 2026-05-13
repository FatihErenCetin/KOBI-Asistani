"""AI ile kişiselleştirilmiş kargo durumu bildirim servisi.

Her status transition için müşteriye Gemini ile yazılmış mesaj gönderir.
LLM yoksa veya hata olursa deterministik template'e düşer. Telegram gönderim
hatası yutulur (logger'a yazılır) — bildirim başarısız olsa bile kargo akışı
etkilenmez.

Commit sonrası best-effort çağrılır:

    old = shipment.status
    await cargo_mock.advance(db, shipment)
    new = shipment.status
    await db.commit()
    if new != old:
        await shipment_notifier.notify_status_change(db, shipment, new)

Kullanıcı bildirimi flag'i: ``SHIPMENT_NOTIFICATIONS_ENABLED``. Default kapalı —
yanlışlıkla canlı müşteriye demo mesajı gitmesin diye.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import llm as llm_core
from app.core.config import settings
from app.db.models import Order, OrderItem, Shipment, ShipmentStatus

logger = logging.getLogger(__name__)


# Status → (kullanıcıya gösterilecek başlık, fallback template)
# Template, AI quota tükendiğinde devreye girer. {name}, {order_id}, {eta},
# {location}, {tracking} placeholder'larıyla doldurulur.
_STATUS_TEMPLATES: dict[ShipmentStatus, tuple[str, str]] = {
    ShipmentStatus.PICKED_UP: (
        "Kargoya verildi",
        "Merhaba {name}! 📦 #{order_id} numaralı siparişiniz kargoya teslim "
        "edildi. Takip numarası: {tracking}. Tahmini teslim: {eta}. İyi günler!",
    ),
    ShipmentStatus.IN_TRANSIT: (
        "Yola çıktı",
        "Merhaba {name}! 🚚 #{order_id} numaralı siparişiniz yola çıktı. "
        "Şu anda: {location}. Tahmini teslim: {eta}.",
    ),
    ShipmentStatus.OUT_FOR_DELIVERY: (
        "Dağıtıma çıktı",
        "Merhaba {name}! 🛵 #{order_id} numaralı siparişiniz bugün dağıtımda. "
        "Yakında elinize ulaşacak. Konum: {location}.",
    ),
    ShipmentStatus.DELIVERED: (
        "Teslim edildi",
        "Merhaba {name}! ✅ #{order_id} numaralı siparişiniz teslim edildi. "
        "Bizi tercih ettiğiniz için teşekkür ederiz. Tekrar görüşmek üzere!",
    ),
}

# AI prompt'u — kısa, sıcak, emojili. Sadece düz metin döndürmeli, JSON değil.
_SYSTEM_PROMPT = (
    "Sen bir Türk KOBİ'sinin müşteri ilişkileri asistanısın. "
    "Müşteriye Telegram üzerinden gönderilecek KISA (en fazla 280 karakter) ve "
    "samimi bir kargo durum mesajı yaz. "
    "Sadece düz metin döndür — JSON, kod bloğu veya markdown KULLANMA. "
    "Mesajda mutlaka: müşteri adı, sipariş numarası, durum bilgisi olsun. "
    "İlgili 1-2 emoji ekle. Resmi değil samimi ol. Aşırı satış pazarlama yapma."
)


async def _ai_compose_message(
    *,
    status: ShipmentStatus,
    name: str,
    order_id: int,
    tracking: str,
    eta: str,
    location: str,
    item_summary: str,
) -> str | None:
    """Gemini ile durum mesajı yaz. Hata/quota → None."""
    if not settings.gemini_api_keys_list:
        return None
    try:
        from google.genai import types

        title, _ = _STATUS_TEMPLATES.get(status, ("Kargo güncellemesi", ""))
        user_input = (
            f"Durum: {title}\n"
            f"Müşteri adı: {name}\n"
            f"Sipariş no: #{order_id}\n"
            f"Takip no: {tracking}\n"
            f"Tahmini teslim: {eta}\n"
            f"Konum: {location}\n"
            f"Sipariş içeriği: {item_summary}"
        )
        response = await llm_core.generate_content_with_fallback(
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_input)],
                )
            ],
            config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
        )
        text = (response.text or "").strip()
        # Markdown fence varsa temizle (modeli kaçırırsa)
        if text.startswith("```"):
            text = text.strip("`").lstrip("text").strip()
        # Çok uzun çıktıyı kırp
        return text[:600] if text else None
    except Exception as e:
        logger.warning("Shipment notifier LLM failed: %s", e)
        return None


def _fallback_message(
    status: ShipmentStatus,
    *,
    name: str,
    order_id: int,
    tracking: str,
    eta: str,
    location: str,
) -> str | None:
    entry = _STATUS_TEMPLATES.get(status)
    if entry is None:
        return None
    _, template = entry
    return template.format(
        name=name,
        order_id=order_id,
        tracking=tracking,
        eta=eta,
        location=location,
    )


def _item_summary(order: Order) -> str:
    """Sipariş kalemlerini kısa bir özet stringe çevir (en fazla 3 kalem)."""
    items = list(order.items or [])
    if not items:
        return "—"
    parts = []
    for it in items[:3]:
        prod_name = it.product.name if it.product else "Ürün"
        parts.append(f"{it.quantity} {prod_name}")
    if len(items) > 3:
        parts.append(f"+{len(items) - 3} kalem")
    return ", ".join(parts)


async def notify_status_change(
    db: AsyncSession, shipment: Shipment, new_status: ShipmentStatus
) -> bool:
    """Kargo durum değişikliği için müşteriye Telegram bildirimi gönder.

    True döner = mesaj denendi (başarılı veya değil log'lanır).
    False döner = bildirim atlandı (flag kapalı, status notifiable değil,
    müşteri telegram_user_id'si yok vb.).

    İdempotency garantisi YOK: aynı status için tekrar tekrar çağrılırsa
    her seferinde mesaj atar. Caller'ın old != new kontrolü yapması beklenir.
    """
    if not settings.SHIPMENT_NOTIFICATIONS_ENABLED:
        return False
    if new_status not in _STATUS_TEMPLATES:
        return False

    # Order + customer + items + each item's product eager-load
    if shipment.order_id is None:
        return False
    res = await db.execute(
        select(Order)
        .where(Order.id == shipment.order_id)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    order = res.scalar_one_or_none()
    if order is None or order.customer is None:
        return False

    tg_id = order.customer.telegram_user_id
    if not tg_id:
        logger.info(
            "Shipment notify skipped: order=%s customer has no telegram_user_id",
            order.id,
        )
        return False

    name = order.customer.name or "müşterimiz"
    tracking = shipment.tracking_no or "—"
    eta = (
        shipment.estimated_delivery.strftime("%d.%m.%Y")
        if shipment.estimated_delivery
        else "—"
    )
    location = shipment.current_location or "—"
    item_summary = _item_summary(order)

    message = await _ai_compose_message(
        status=new_status,
        name=name,
        order_id=order.id,
        tracking=tracking,
        eta=eta,
        location=location,
        item_summary=item_summary,
    )
    if not message:
        message = _fallback_message(
            new_status,
            name=name,
            order_id=order.id,
            tracking=tracking,
            eta=eta,
            location=location,
        )
    if not message:
        return False

    try:
        from app.integrations.telegram_client import telegram_client

        await telegram_client.send_message(tg_id, message, parse_mode="")
        logger.info(
            "Shipment notify sent: tg=%s order=%s status=%s",
            tg_id, order.id, new_status.value,
        )
        return True
    except Exception:
        logger.exception(
            "Shipment notify Telegram send failed: order=%s status=%s",
            order.id, new_status.value,
        )
        return False


async def notify_delay(
    *,
    telegram_user_id: int,
    customer_name: str,
    order_id: int,
    days_overdue: int,
    current_location: str | None,
    item_summary: str,
) -> bool:
    """Gecikme için AI ile özür mesajı yaz. proactive_risk_scanner çağırır.

    Statik template'in yerine geçer. Quota yoksa fallback'e düşer.
    """
    if not settings.PROACTIVE_NOTIFICATIONS_ENABLED:
        return False

    name = customer_name or "müşterimiz"
    location = current_location or "yolda"

    # Özür mesajı için ayrı bir özelleştirilmiş prompt
    apology_system = (
        "Sen bir Türk KOBİ'sinin müşteri ilişkileri asistanısın. "
        "Gecikmiş bir kargo için müşteriye Telegram'dan kısa (en fazla 320 karakter) "
        "ve içten bir ÖZÜR mesajı yaz. "
        "Müşterinin sinirini almaya çalış ama abartma. "
        "Sadece düz metin döndür. Mesajda mutlaka: müşteri adı, sipariş no, "
        "gecikme süresi, mevcut konum bilgisi olsun. "
        "Gerçekçi ol — kesin söz verme ('mutlaka', 'kesinlikle' gibi)."
    )

    ai_text: str | None = None
    if settings.gemini_api_keys_list:
        try:
            from google.genai import types

            user_input = (
                f"Müşteri adı: {name}\n"
                f"Sipariş no: #{order_id}\n"
                f"Gecikme: {days_overdue} gün\n"
                f"Mevcut konum: {location}\n"
                f"Sipariş içeriği: {item_summary}"
            )
            response = await llm_core.generate_content_with_fallback(
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_input)],
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=apology_system
                ),
            )
            text = (response.text or "").strip()
            if text.startswith("```"):
                text = text.strip("`").lstrip("text").strip()
            ai_text = text[:600] if text else None
        except Exception as e:
            logger.warning("Delay notifier LLM failed: %s", e)

    message = ai_text or (
        f"Merhaba {name}, #{order_id} numaralı siparişinizin teslim tarihi "
        f"{days_overdue} gün geçti (mevcut konum: {location}). Gecikme için "
        "özür dileriz, durumu yakından takip ediyoruz."
    )

    try:
        from app.integrations.telegram_client import telegram_client

        await telegram_client.send_message(
            telegram_user_id, message, parse_mode=""
        )
        logger.info(
            "Delay notify sent: tg=%s order=%s days=%s",
            telegram_user_id, order_id, days_overdue,
        )
        return True
    except Exception:
        logger.exception("Delay notify Telegram send failed: order=%s", order_id)
        return False
