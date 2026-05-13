"""Prediktif stok tahmin job'i.

- Her aktif urun icin gunluk satis hizini hesaplar (product_analytics)
- N gun icinde bitecek urunleri tespit eder
- Admin Telegram'a ozet bildirim gonderir (varsa ADMIN_TELEGRAM_ID)
- Reorder helper + mail_template ile her ürün için draft mail metni üretip log'a yazar
  (Gmail entegrasyonu opsiyonel; otomatik gondermez — sistem dostane kalir)

Bu job 'sabah brifingi' ile cakismaz; daha sik (her 6 saatte) ve sadece kritik
stok azalmasi varsa bildirim gonderir.
"""

import logging
from datetime import datetime

from sqlalchemy import select

from app.core.config import settings
from app.db.crud import product_analytics as analytics_crud
from app.db.crud import product_suppliers as ps_crud
from app.db.models import Product
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client
from app.services.mail_template import draft_reorder_mail

logger = logging.getLogger(__name__)

# Bu kadar gün içinde tükenecek ürünler kritik sayılır
DEFAULT_FORECAST_DAYS = 7


def _fmt_tr_amount(amount: float) -> str:
    return (
        f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        + " TL"
    )


async def forecast_at_risk_products(
    forecast_days: int = DEFAULT_FORECAST_DAYS,
) -> list[dict]:
    """N gun icinde tukenecek aktif urunleri analytics'ten cikarir.

    Returns: [{product_id, name, unit, stock, daily_velocity, days_of_stock,
               estimated_run_out_at, suggested_qty, preferred_supplier_name}]
    """
    at_risk: list[dict] = []
    async with SessionLocal() as db:
        res = await db.execute(
            select(Product).where(Product.is_active.is_(True))
        )
        products = list(res.scalars())
        for p in products:
            data = await analytics_crud.for_product(db, p)
            dos = data.get("days_of_stock")
            velocity = data.get("daily_velocity") or 0.0
            # Hiç satış yoksa ve eşik altıysa yine de listele
            if dos is None and p.stock <= p.low_stock_threshold:
                at_risk.append(
                    {
                        "product_id": p.id,
                        "name": p.name,
                        "unit": p.unit,
                        "stock": p.stock,
                        "daily_velocity": 0.0,
                        "days_of_stock": None,
                        "suggested_qty": max(p.low_stock_threshold * 2, 10),
                        "reason": "low_threshold_no_sales",
                    }
                )
                continue
            if dos is None:
                continue
            if dos > forecast_days:
                continue
            suggested = max(
                (p.max_stock or p.low_stock_threshold * 2) - p.stock,
                p.low_stock_threshold,
            )
            # Tercih edilen tedarikçi
            links = await ps_crud.list_for_product(db, p.id)
            preferred = next((l for l in links if l.is_preferred), None) or (
                links[0] if links else None
            )
            at_risk.append(
                {
                    "product_id": p.id,
                    "name": p.name,
                    "unit": p.unit,
                    "stock": p.stock,
                    "daily_velocity": velocity,
                    "days_of_stock": dos,
                    "suggested_qty": round(suggested, 2),
                    "preferred_supplier_id": preferred.supplier_id if preferred else None,
                    "preferred_supplier_name": (
                        preferred.supplier.name
                        if preferred and preferred.supplier
                        else None
                    ),
                    "last_unit_cost": preferred.last_unit_cost if preferred else None,
                    "lead_time_days": preferred.lead_time_days if preferred else None,
                    "reason": "forecast_threshold",
                }
            )
    at_risk.sort(
        key=lambda r: (
            r["days_of_stock"] if r["days_of_stock"] is not None else 999
        )
    )
    return at_risk


def _build_admin_summary(items: list[dict], forecast_days: int) -> str:
    """Admin Telegram mesaji icin ozet metin."""
    if not items:
        return ""
    lines = [
        f"📊 Stok tahmin uyarısı ({forecast_days} gün penceresi):",
        "",
    ]
    for r in items[:10]:
        dos = r["days_of_stock"]
        if dos is None:
            line = f"• <b>{r['name']}</b>: eşik altı ({r['stock']} {r['unit']})"
        else:
            line = (
                f"• <b>{r['name']}</b>: {r['stock']} {r['unit']} kaldı, "
                f"~{dos:.0f} gün dayanır. Önerilen: {r['suggested_qty']} {r['unit']}"
            )
        if r.get("preferred_supplier_name"):
            line += f" ({r['preferred_supplier_name']})"
        lines.append(line)
    if len(items) > 10:
        lines.append(f"… ve {len(items) - 10} ürün daha")
    return "\n".join(lines)


async def run_forecast_job(forecast_days: int = DEFAULT_FORECAST_DAYS) -> dict:
    """APScheduler tetikleyici fonksiyon."""
    items = await forecast_at_risk_products(forecast_days)
    drafts_logged = 0

    # Admin'e ozet
    if items and settings.ADMIN_TELEGRAM_ID:
        text = _build_admin_summary(items, forecast_days)
        try:
            await telegram_client.send_message(
                int(settings.ADMIN_TELEGRAM_ID), text
            )
        except Exception:
            logger.exception("Admin forecast notify failed")

    # Her risk için draft mail log'la (Gmail göndermez, sadece üretir)
    for r in items:
        if not r.get("preferred_supplier_name"):
            continue
        try:
            draft = draft_reorder_mail(
                supplier_name=r["preferred_supplier_name"],
                product_name=r["name"],
                order_qty=r["suggested_qty"],
                unit=r["unit"],
                last_unit_cost=r.get("last_unit_cost"),
                lead_time_days=r.get("lead_time_days"),
                admin_name="KOBI Asistani",
            )
            drafts_logged += 1
            logger.info(
                "Reorder draft for %s → %s: %s",
                r["name"], r["preferred_supplier_name"], draft["subject"],
            )
        except Exception:
            logger.exception("Mail draft failed for %s", r["name"])

    summary = {
        "at_risk_count": len(items),
        "drafts_logged": drafts_logged,
        "forecast_days": forecast_days,
        "run_at": datetime.utcnow().isoformat(),
    }
    logger.info("Stock forecast job complete: %s", summary)
    return summary
