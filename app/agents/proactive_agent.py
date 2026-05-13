"""Proaktif bildirim ajani.

detect_delays() ciktisini alir, her gecikme durumu icin:
- Musteri Telegram mesaji uretir (LLM)
- Yonetici ozet mesaji uretir (LLM)
- Senaryo 2 icin kargo firmasi iletisim taslagi uretir (LLM)
- Hepsini Telegram uzerinden iletir
"""

import logging

from app.core.config import settings
from app.core.llm import ToolSpec, run_agent_loop
from app.integrations.telegram_client import telegram_client
from app.jobs.delay_detector import detect_delays

logger = logging.getLogger(__name__)

CUSTOMER_SYSTEM_PROMPT = """Sen bir KOBİ'nin müşteri hizmetleri asistanısın.
Müşteriye kargo gecikmesi hakkında samimi, kısa ve saygılı bir Telegram mesajı yaz.
Türkçe karakterleri tam kullan. Mesaj maksimum 3 cümle olsun.
Özür dile, mevcut konumu belirt, çözüm için çalıştığınızı söyle.
JSON veya format kullanma, düz metin yaz."""

ADMIN_OVERDUE_PROMPT = """Sen bir iş zekası asistanısın.
Yöneticiye geciken kargo hakkında özlü bir Türkçe durum raporu yaz.
Sipariş no, müşteri adı, kaç gün gecikmeli, mevcut konum bilgilerini kullan.
Aksiyon öner. Maksimum 4 cümle, düz metin."""

ADMIN_STALE_PROMPT = """Sen bir iş zekası asistanısın.
Yöneticiye hareketsiz kalan kargo hakkında acil durum raporu yaz.
Kaç saattir hareket yok, son konum, kargo firması bilgilerini belirt.
Kargo firmasıyla iletişime geçilmesi gerektiğini vurgula. Maksimum 4 cümle, düz metin."""

CARRIER_CONTACT_PROMPT = """Sen bir işletme adına kargo firmasına yazıyorsun.
Resmi, kısa ve net bir Türkçe iletişim taslağı yaz.
Takip numarasını, son bilinen konumu ve kaç saattir güncelleme olmadığını belirt.
Acil durum bildirimi ve çözüm talebi içersin. Maksimum 5 cümle, düz metin."""


async def _llm_message(system: str, user: str) -> str:
    """LLM'den tek bir metin mesaji uretir."""
    result = await run_agent_loop(
        system_prompt=system,
        user_message=user,
        tools=[],
    )
    return (result.text or "").strip()


async def _notify_customer(item: dict, message: str) -> None:
    tg_id = item["telegram_user_id"]
    try:
        await telegram_client.send_message(tg_id, message)
        logger.info("Customer notified: tg=%s order=%s", tg_id, item["order_id"])
    except Exception:
        logger.exception("Failed to notify customer tg=%s", tg_id)


async def _notify_admin(message: str) -> None:
    admin_id = settings.ADMIN_TELEGRAM_ID
    if not admin_id:
        logger.warning("ADMIN_TELEGRAM_ID not set, skipping admin notification")
        return
    try:
        await telegram_client.send_message(int(admin_id), message)
    except Exception:
        logger.exception("Failed to notify admin")


async def handle_overdue(item: dict) -> None:
    """Senaryo 1: Teslim tarihi gecmis."""
    items_str = ", ".join(item["items"]) if item["items"] else "ürünleriniz"
    days_late = item.get("days_late", 1)
    location = item["current_location"] or "bilinmiyor"

    # Musteri mesaji
    customer_prompt = (
        f"Müşteri adı: {item['customer_name']}\n"
        f"Sipariş no: {item['order_id']}\n"
        f"Ürünler: {items_str}\n"
        f"Gecikme: {days_late} gün\n"
        f"Mevcut konum: {location}\n"
        f"Kargo firması: {item['carrier']}\n"
        f"Takip no: {item['tracking_no']}"
    )
    customer_msg = await _llm_message(CUSTOMER_SYSTEM_PROMPT, customer_prompt)
    await _notify_customer(item, customer_msg)

    # Yonetici mesaji
    admin_prompt = (
        f"Sipariş #{item['order_id']} - {item['customer_name']}\n"
        f"Ürünler: {items_str}\n"
        f"Gecikme: {days_late} gün\n"
        f"Taahhüt tarihi: {item['promised_delivery']}\n"
        f"Mevcut konum: {location}\n"
        f"Kargo: {item['carrier']} / {item['tracking_no']}"
    )
    admin_msg = await _llm_message(ADMIN_OVERDUE_PROMPT, admin_prompt)
    await _notify_admin(f"⚠️ GECİKME ALARMI\n\n{admin_msg}")


async def handle_stale(item: dict) -> None:
    """Senaryo 2: Kargo hareketsiz, kargo firmasiyla iletisim gerekli."""
    items_str = ", ".join(item["items"]) if item["items"] else "ürünleriniz"
    hours_stale = item.get("hours_stale", 48)
    location = item["current_location"] or "bilinmiyor"

    # Musteri mesaji
    customer_prompt = (
        f"Müşteri adı: {item['customer_name']}\n"
        f"Sipariş no: {item['order_id']}\n"
        f"Ürünler: {items_str}\n"
        f"Durum: Kargo {hours_stale} saattir güncelleme almadı\n"
        f"Son bilinen konum: {location}\n"
        f"Kargo firması: {item['carrier']}"
    )
    customer_msg = await _llm_message(CUSTOMER_SYSTEM_PROMPT, customer_prompt)
    await _notify_customer(item, customer_msg)

    # Kargo firmasi taslagi
    carrier_prompt = (
        f"Kargo firması: {item['carrier']}\n"
        f"Takip numarası: {item['tracking_no']}\n"
        f"Son güncelleme: {hours_stale} saat önce\n"
        f"Son bilinen konum: {location}\n"
        f"Sipariş no: {item['order_id']}"
    )
    carrier_draft = await _llm_message(CARRIER_CONTACT_PROMPT, carrier_prompt)

    # Yonetici mesaji - kargo taslagi ile birlikte
    admin_prompt = (
        f"Sipariş #{item['order_id']} - {item['customer_name']}\n"
        f"Ürünler: {items_str}\n"
        f"Hareketsiz: {hours_stale} saat\n"
        f"Son konum: {location}\n"
        f"Kargo: {item['carrier']} / {item['tracking_no']}"
    )
    admin_msg = await _llm_message(ADMIN_STALE_PROMPT, admin_prompt)

    full_admin_msg = (
        f"🚨 ACİL: HAREKETSİZ KARGO\n\n"
        f"{admin_msg}\n\n"
        f"📋 Kargo firması iletişim taslağı:\n"
        f"{carrier_draft}"
    )
    await _notify_admin(full_admin_msg)


async def run_proactive_notifications() -> None:
    """Ana job fonksiyonu - scheduler tarafindan cagrilir."""
    logger.info("Running proactive delay notification job")
    try:
        delays = await detect_delays()
    except Exception:
        logger.exception("delay_detector failed")
        return

    for item in delays["overdue"]:
        try:
            await handle_overdue(item)
        except Exception:
            logger.exception("handle_overdue failed for order %s", item.get("order_id"))

    for item in delays["stale"]:
        try:
            await handle_stale(item)
        except Exception:
            logger.exception("handle_stale failed for order %s", item.get("order_id"))

    total = len(delays["overdue"]) + len(delays["stale"])
    logger.info("Proactive notifications done: %d sent", total)
