"""Prediktif stok yonetimi job'i.

Gecmis satis verisine bakarak her urun icin:
- Gunluk ortalama tuketimi hesaplar
- Kac gunde tukenecegini tahmin eder
- Esik altina dusecek urunleri onceden tespit eder
- Yoneticiye Telegram bildirimi gonderir
- LLM ile tedarikci siparis mail taslagi uretir
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.llm import run_agent_loop
from app.db.models import Order, OrderItem, OrderStatus, Product
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client

logger = logging.getLogger(__name__)

# Tedarikci mail adresi - gercek projede DB'den veya config'den gelir
SUPPLIER_EMAIL = ""  # .env'den okunacak

# Kac gun icerisinde tukenmesi beklenen urunler icin uyari uret
FORECAST_DAYS = 7
# Analize dahil edilecek gecmis gun sayisi
LOOKBACK_DAYS = 30


ADMIN_ALERT_PROMPT = """Sen bir KOBİ'nin stok yönetimi asistanısın.
Yöneticiye düşük stok uyarısı hakkında kısa ve net bir Türkçe mesaj yaz.
Türkçe karakterleri tam kullan. Emoji kullanabilirsin (az).
Ürün adı, mevcut stok, tahmini tükenme süresi ve önerilen sipariş miktarını belirt.
Maksimum 4 cümle, düz metin."""

SUPPLIER_MAIL_PROMPT = """Sen bir KOBİ adına tedarikçiye sipariş maili yazıyorsun.
Resmi, kısa ve net Türkçe bir mail taslağı yaz.
Konu satırı dahil yaz. Ürün adı, talep edilen miktar ve teslim aciliyetini belirt.
Maksimum 6 cümle."""


async def _get_sales_velocity(db, product_id: int, lookback_days: int) -> float:
    """Urunun gunluk ortalama satis miktarini hesaplar."""
    since = datetime.utcnow() - timedelta(days=lookback_days)
    result = await db.execute(
        select(func.coalesce(func.sum(OrderItem.quantity), 0.0))
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.product_id == product_id)
        .where(Order.created_at >= since)
        .where(Order.status != OrderStatus.CANCELLED)
    )
    total_sold = float(result.scalar_one())
    return total_sold / lookback_days if lookback_days > 0 else 0.0


async def _forecast_stock() -> list[dict]:
    """Tum urunler icin stok tahminini hesaplar, riskli olanlari doner."""
    at_risk = []

    async with SessionLocal() as db:
        products_res = await db.execute(select(Product))
        products = list(products_res.scalars())

        for p in products:
            daily_velocity = await _get_sales_velocity(db, p.id, LOOKBACK_DAYS)

            if daily_velocity <= 0:
                # Satisi olmayan urun, sadece esik altindaysa ekle
                if p.stock <= p.low_stock_threshold:
                    at_risk.append({
                        "product_id": p.id,
                        "name": p.name,
                        "unit": p.unit,
                        "stock": p.stock,
                        "threshold": p.low_stock_threshold,
                        "price": p.price,
                        "daily_velocity": 0.0,
                        "days_until_empty": None,
                        "days_until_threshold": None,
                        "already_low": True,
                        "suggested_order_qty": p.low_stock_threshold * 2,
                    })
                continue

            days_until_empty = p.stock / daily_velocity
            days_until_threshold = (
                (p.stock - p.low_stock_threshold) / daily_velocity
                if p.stock > p.low_stock_threshold else 0
            )

            # FORECAST_DAYS icerisinde esige ulasilacaksa uyar
            if days_until_threshold <= FORECAST_DAYS or p.stock <= p.low_stock_threshold:
                # 2 haftalik ortalama satis kadar siparis ver
                suggested_qty = round(daily_velocity * 14, 1)

                at_risk.append({
                    "product_id": p.id,
                    "name": p.name,
                    "unit": p.unit,
                    "stock": p.stock,
                    "threshold": p.low_stock_threshold,
                    "price": p.price,
                    "daily_velocity": round(daily_velocity, 2),
                    "days_until_empty": round(days_until_empty, 1),
                    "days_until_threshold": round(days_until_threshold, 1),
                    "already_low": p.stock <= p.low_stock_threshold,
                    "suggested_order_qty": suggested_qty,
                })

    # En kritik olandan sirala
    at_risk.sort(key=lambda x: x["days_until_threshold"] or 0)
    return at_risk


async def _generate_admin_alert(products: list[dict]) -> str:
    """Yonetici icin ozet uyari mesaji uretir."""
    lines = []
    for p in products:
        if p["already_low"]:
            status = "STOKTA YETERSİZ"
        else:
            status = f"~{p['days_until_threshold']} günde eşiğe ulaşacak"

        velocity_str = (
            f"{p['daily_velocity']} {p['unit']}/gün"
            if p["daily_velocity"] > 0 else "satış verisi yok"
        )
        lines.append(
            f"- {p['name']}: {p['stock']} {p['unit']} mevcut | "
            f"{velocity_str} | {status} | "
            f"Önerilen sipariş: {p['suggested_order_qty']} {p['unit']}"
        )

    user_prompt = (
        f"{len(products)} ürün kritik stok seviyesine yaklaşıyor:\n\n"
        + "\n".join(lines)
        + "\n\nYöneticiye kısa bir uyarı ve aksiyon özeti yaz."
    )

    result = await run_agent_loop(
        system_prompt=ADMIN_ALERT_PROMPT,
        user_message=user_prompt,
        tools=[],
    )
    return (result.text or "").strip()


async def _generate_supplier_draft(product: dict) -> str:
    """Tek urun icin tedarikci mail taslagi uretir."""
    user_prompt = (
        f"Ürün: {product['name']}\n"
        f"Talep edilen miktar: {product['suggested_order_qty']} {product['unit']}\n"
        f"Mevcut stok: {product['stock']} {product['unit']}\n"
        f"Günlük tüketim: {product['daily_velocity']} {product['unit']}/gün\n"
        f"Tahmini tükenme: {product['days_until_empty']} gün\n"
        f"Aciliyet: {'ACİL' if product['already_low'] else 'Normal'}"
    )
    result = await run_agent_loop(
        system_prompt=SUPPLIER_MAIL_PROMPT,
        user_message=user_prompt,
        tools=[],
    )
    return (result.text or "").strip()


async def run_stock_forecast() -> None:
    """Ana job fonksiyonu - scheduler tarafindan cagrilir."""
    logger.info("Running predictive stock forecast job")
    admin_id = settings.ADMIN_TELEGRAM_ID
    if not admin_id:
        logger.warning("ADMIN_TELEGRAM_ID not set, skipping stock forecast")
        return

    try:
        at_risk = await _forecast_stock()
    except Exception:
        logger.exception("Failed to forecast stock")
        return

    if not at_risk:
        logger.info("Stock forecast: all products OK")
        return

    logger.info("Stock forecast: %d products at risk", len(at_risk))

    # Ozet uyari
    try:
        alert_msg = await _generate_admin_alert(at_risk)
        await telegram_client.send_message(
            int(admin_id),
            f"📦 TAHMİNLİ STOK UYARISI\n\n{alert_msg}"
        )
    except Exception:
        logger.exception("Failed to send stock alert")
        return

    # En kritik 3 urun icin tedarikci mail taslagi + gercek mail
    from app.core.config import settings as _settings
    supplier_email = getattr(_settings, "SUPPLIER_EMAIL", "")

    for product in at_risk[:3]:
        try:
            draft = await _generate_supplier_draft(product)

            # Yoneticiye taslagi goster
            await telegram_client.send_message(
                int(admin_id),
                "📧 Tedarikçi Mail Taslağı — " + product["name"] + "\n\n" + draft
            )

            # Gercek mail gonder (supplier_email varsa)
            if supplier_email:
                from app.integrations.gmail_client import send_supplier_email
                mail_result = await send_supplier_email(
                    supplier_email=supplier_email,
                    product_name=product["name"],
                    quantity=product["suggested_order_qty"],
                    unit=product["unit"],
                    urgency="urgent" if product["already_low"] else "normal",
                    draft_text=draft,
                )
                if mail_result.get("success"):
                    await telegram_client.send_message(
                        int(admin_id),
                        "✅ Tedarikçiye mail gönderildi: " + supplier_email
                    )
                    logger.info("Supplier email sent for %s", product["name"])
                else:
                    logger.warning("Supplier email failed: %s", mail_result.get("error"))
        except Exception:
            logger.exception(
                "Failed to generate supplier draft for %s", product["name"]
            )
