"""Proaktif risk tarayıcı — agentic akış.

Akış:
1. Deterministik finder'lar anomalileri bulur (risk_detectors).
2. Her bulgu için Gemini'ye 'müşteri perspektifinden konu + açıklama yaz' der.
3. Mükerrer kontrol (aynı entity için son 24 saatte kayıt varsa atlanır).
4. CustomerComplaint kaydı oluşturur (auto_generated=True).

LLM hata verirse: deterministik şablon kullanılır (LLM-free fallback).
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.crud import complaints as complaints_crud
from app.db.models import CustomerComplaint
from app.services import risk_detectors

logger = logging.getLogger(__name__)


# Mükerrer önleme: aynı entity + source için bu kadar saat içinde tekrar yazma
DEDUPE_HOURS = 24


async def _has_recent_complaint(
    db: AsyncSession,
    *,
    source: str,
    related_entity_type: str,
    related_entity_id: int,
) -> bool:
    cutoff = datetime.utcnow() - timedelta(hours=DEDUPE_HOURS)
    res = await db.execute(
        select(CustomerComplaint.id)
        .where(
            CustomerComplaint.source == source,
            CustomerComplaint.related_entity_type == related_entity_type,
            CustomerComplaint.related_entity_id == related_entity_id,
            CustomerComplaint.created_at >= cutoff,
            CustomerComplaint.resolved.is_(False),
        )
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


async def _llm_narrate(category: str, payload: dict) -> tuple[str, str]:
    """Gemini'ye konu + açıklama yaz. Hata olursa deterministik şablon."""
    fallback_subject, fallback_desc = _fallback_narrate(category, payload)
    if not settings.GEMINI_API_KEY:
        return fallback_subject, fallback_desc
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            f"Aşağıdaki risk durumu için müşteri hizmetleri perspektifinden "
            f"bir 'Konu' satırı ve 2-4 cümlelik 'Açıklama' yaz. Türkçe konuş, "
            f"Türkçe karakterleri tam kullan (ş, ç, ğ, ü, ö, ı, İ). "
            f"Açıklamada somut sayıları belirt ve aksiyon öner. "
            f"Çıktıyı şu formatta ver, başka hiçbir şey yazma:\n"
            f"KONU: <başlık 80 karakter altı>\n"
            f"AÇIKLAMA: <2-4 cümle>\n\n"
            f"Kategori: {category}\n"
            f"Veri: {payload}"
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt
        )
        text = (response.text or "").strip()
        subject = fallback_subject
        description = fallback_desc
        for line in text.splitlines():
            line = line.strip()
            if line.upper().startswith("KONU:"):
                subject = line.split(":", 1)[1].strip()[:200]
            elif line.upper().startswith("AÇIKLAMA:") or line.upper().startswith("ACIKLAMA:"):
                description = line.split(":", 1)[1].strip()[:1900]
        return subject, description
    except Exception as e:
        logger.warning("LLM narrate failed for %s: %s", category, e)
        return fallback_subject, fallback_desc


def _fallback_narrate(category: str, p: dict) -> tuple[str, str]:
    """LLM olmadan veya hata durumunda yedek metin."""
    if category == "shipment_delay":
        cust = p.get("customer_name") or f"Müşteri #{p.get('customer_id')}"
        return (
            f"Kargo gecikmesi: Sipariş #{p['order_id']} ({cust})",
            f"{cust} için #{p['order_id']} numaralı siparişin kargosu "
            f"({p['tracking_no']}) {p['days_overdue']} gündür beklenen teslim "
            f"tarihini geçti. Durum: {p['current_status']}. Müşteriyi proaktif "
            f"olarak arayıp bilgi vermek gerekiyor.",
        )
    if category == "slow_shipment":
        cust = p.get("customer_name") or f"Müşteri #{p.get('customer_id')}"
        return (
            f"Yavaş kargo: Sipariş #{p['order_id']} ({cust})",
            f"#{p['order_id']} numaralı siparişin kargosu {p['age_days']} gündür "
            f"yolda. Sistem ortalaması {p['avg_age_days']} gün. Kargo şirketiyle "
            f"iletişime geçilmesi öneriliyor.",
        )
    if category == "stale_pending":
        cust = p.get("customer_name") or f"Müşteri #{p.get('customer_id')}"
        return (
            f"Bekleyen sipariş: #{p['order_id']} ({cust}, {p['hours_pending']} saat)",
            f"#{p['order_id']} numaralı sipariş {p['hours_pending']} saattir "
            f"hazırlanmayı bekliyor. Tutar: {p['total']} TL. "
            f"İçerik: {p['items_summary']}. Müşteri sabırsızlanabilir.",
        )
    if category == "repeat_complainer":
        cust = p.get("customer_name") or f"Müşteri #{p.get('customer_id')}"
        return (
            f"Tekrarlayan şikayet: {cust} ({p['complaint_count']} kez)",
            f"{cust} son {p['since_days']} günde {p['complaint_count']} ayrı "
            f"şikayet sinyali oluşturdu. En yüksek risk skoru "
            f"%{int(p['max_risk_score'] * 100)}. Müşteri ilişkisi sorgulanmalı.",
        )
    if category == "dormant_customer":
        cust = p.get("customer_name") or f"Müşteri #{p.get('customer_id')}"
        return (
            f"Sessizleşen müşteri: {cust} ({p['days_silent']} gündür)",
            f"{cust} öncesinde {p['prior_order_count']} sipariş ile düzenli "
            f"alışveriş yapıyordu. Toplam harcama: {p['total_spend']} TL. "
            f"Son {p['days_silent']} gündür sipariş yok. Tekrar etkileşim önerilir.",
        )
    return (f"Risk bulgu: {category}", str(p)[:1900])


# Her kategori için sabit risk skoru (saatlik tetiklenirken stabilite)
_CATEGORY_SCORES = {
    "shipment_delay": 0.85,
    "slow_shipment": 0.7,
    "stale_pending": 0.75,
    "repeat_complainer": 0.9,
    "dormant_customer": 0.6,
}


async def _notify_delay_to_customer(finding: dict) -> None:
    """Kargo gecikmesi tespit edilince müşteriye Telegram özür mesajı gönder.

    PROACTIVE_NOTIFICATIONS_ENABLED kapalıysa hiçbir şey yapmaz. Müşterinin
    telegram_user_id'si finding'den okunur (find_delayed_shipments dolduruyor).
    """
    if not settings.PROACTIVE_NOTIFICATIONS_ENABLED:
        return
    tg_id = finding.get("telegram_user_id")
    if not tg_id:
        return
    try:
        from app.integrations.telegram_client import telegram_client

        order_id = finding.get("order_id")
        days = finding.get("days_overdue", 1)
        location = finding.get("current_location") or "yolda"
        name = finding.get("customer_name") or "müşterimiz"
        msg = (
            f"Merhaba {name}, #{order_id} numaralı siparişinizin "
            f"kargo teslim tarihi {days} gün geçti (mevcut konum: {location}). "
            f"Gecikme için özür dileriz. Durumu yakından takip ediyoruz ve "
            f"en kısa zamanda elinize ulaşması için kargo firmasıyla görüşüyoruz."
        )
        await telegram_client.send_message(tg_id, msg)
        logger.info(
            "Delay apology sent: tg=%s order=%s days_overdue=%s",
            tg_id, order_id, days,
        )
    except Exception:
        logger.exception("Delay notification to customer failed")


async def _notify_delay_to_admin(finding: dict) -> None:
    """Admin'e geciken kargo özet bildirimi."""
    if not settings.PROACTIVE_NOTIFICATIONS_ENABLED:
        return
    if not settings.ADMIN_TELEGRAM_ID:
        return
    try:
        from app.integrations.telegram_client import telegram_client

        msg = (
            f"⚠️ Kargo gecikme alarmı\n\n"
            f"Sipariş #{finding.get('order_id')} ({finding.get('customer_name')})\n"
            f"Takip: {finding.get('tracking_no')} ({finding.get('carrier')})\n"
            f"Gecikme: {finding.get('days_overdue')} gün\n"
            f"Mevcut konum: {finding.get('current_location') or 'bilinmiyor'}\n"
            f"Müşteriye otomatik özür mesajı iletildi."
        )
        await telegram_client.send_message(int(settings.ADMIN_TELEGRAM_ID), msg)
    except Exception:
        logger.exception("Admin delay notification failed")


async def _process_findings(
    db: AsyncSession,
    *,
    category: str,
    entity_type: str,
    findings: list[dict],
    entity_id_key: str,
) -> int:
    """Bir kategori için tüm bulguları işle: dedupe + LLM + kayıt + (delay ise) Telegram."""
    created = 0
    for finding in findings:
        entity_id = finding.get(entity_id_key)
        if entity_id is None:
            continue
        already = await _has_recent_complaint(
            db,
            source=category,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
        )
        if already:
            continue
        subject, description = await _llm_narrate(category, finding)
        await complaints_crud.create_auto(
            db,
            customer_id=finding.get("customer_id"),
            subject=subject,
            description=description,
            risk_score=_CATEGORY_SCORES.get(category, 0.7),
            source=category,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            signals=[],
        )
        created += 1

        # Side effect: shipment_delay için müşteri + admin Telegram bildirimi
        if category == "shipment_delay":
            await _notify_delay_to_customer(finding)
            await _notify_delay_to_admin(finding)

    return created


async def scan_and_report(db: AsyncSession) -> dict:
    """Tum kategorileri tara, bulgulari kayit altina al, ozet doner."""
    summary = {"shipment_delay": 0, "slow_shipment": 0, "stale_pending": 0,
               "repeat_complainer": 0, "dormant_customer": 0}

    delayed = await risk_detectors.find_delayed_shipments(db)
    summary["shipment_delay"] = await _process_findings(
        db, category="shipment_delay", entity_type="shipment",
        findings=delayed, entity_id_key="shipment_id",
    )

    slow = await risk_detectors.find_slow_shipments(db)
    summary["slow_shipment"] = await _process_findings(
        db, category="slow_shipment", entity_type="shipment",
        findings=slow, entity_id_key="shipment_id",
    )

    stale = await risk_detectors.find_stale_pending_orders(db)
    summary["stale_pending"] = await _process_findings(
        db, category="stale_pending", entity_type="order",
        findings=stale, entity_id_key="order_id",
    )

    repeats = await risk_detectors.find_repeat_complainers(db)
    summary["repeat_complainer"] = await _process_findings(
        db, category="repeat_complainer", entity_type="customer",
        findings=repeats, entity_id_key="customer_id",
    )

    dormant = await risk_detectors.find_dormant_customers(db)
    summary["dormant_customer"] = await _process_findings(
        db, category="dormant_customer", entity_type="customer",
        findings=dormant, entity_id_key="customer_id",
    )

    await db.commit()
    total = sum(summary.values())
    logger.info("Risk scan complete: %s (toplam %d)", summary, total)
    summary["total"] = total
    return summary
