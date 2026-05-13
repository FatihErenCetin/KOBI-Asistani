"""SKT yaklasan lot'lar icin AI aksiyon advisor agent.

Akis:
1. find_expiring_lots ile lot'lari topla.
2. Her lot icin context zenginlestir:
   - product analytics (gunluk satis hizi, kaç günde tüketilir)
   - stok bakiyesi (depo bazli)
   - musteri histosu (bu urunu dusenli alanlar)
3. Gemini'ye JSON formatinda 1-3 aksiyon onerisi istek.
4. LotAction olarak kaydet (mukerrer kontrol: ayni lot icin pending action varsa atla).

LLM hata verirse: deterministik fallback (SKT gun sayisi ve velocity'ye gore).
"""

import json
import logging
from datetime import date, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.crud import product_analytics as analytics_crud
from app.db.crud import stock_lots as lots_crud
from app.db.models import (
    LotAction,
    LotActionStatus,
    LotActionType,
    Order,
    OrderItem,
    OrderStatus,
    StockLot,
)

logger = logging.getLogger(__name__)


async def _gather_lot_context(db: AsyncSession, lot: StockLot) -> dict:
    """Lot'la ilgili tüm zenginleştirici verileri topla."""
    analytics = await analytics_crud.for_product(db, lot.product)
    velocity = analytics.get("daily_velocity", 0) or 0
    days_left = (lot.expiry_date - date.today()).days if lot.expiry_date else None
    natural_consumption_days = (
        (lot.quantity / velocity) if velocity > 0 else None
    )

    # Bu ürünü alan müşteri sayısı (son 90 günde)
    recent_buyers = await db.execute(
        select(func.count(func.distinct(Order.customer_id)))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(
            OrderItem.product_id == lot.product_id,
            Order.status != OrderStatus.CANCELLED,
        )
    )
    n_buyers = int(recent_buyers.scalar_one() or 0)

    return {
        "lot_id": lot.id,
        "lot_number": lot.lot_number,
        "product_name": lot.product.name if lot.product else "?",
        "product_id": lot.product_id,
        "unit": lot.product.unit if lot.product else "?",
        "price": lot.product.price if lot.product else 0,
        "warehouse_name": lot.warehouse.name if lot.warehouse else "?",
        "quantity": lot.quantity,
        "expiry_date": lot.expiry_date.isoformat() if lot.expiry_date else None,
        "days_until_expiry": days_left,
        "daily_velocity": velocity,
        "natural_consumption_days": (
            round(natural_consumption_days, 1)
            if natural_consumption_days is not None
            else None
        ),
        "will_naturally_consume_in_time": (
            natural_consumption_days is not None
            and days_left is not None
            and natural_consumption_days <= days_left
        ),
        "recent_buyer_count": n_buyers,
    }


def _fallback_actions(ctx: dict) -> list[dict]:
    """LLM yoksa veya hata olursa deterministik öneriler."""
    days_left = ctx["days_until_expiry"]
    qty = ctx["quantity"]
    velocity = ctx["daily_velocity"]
    name = ctx["product_name"]

    if days_left is None or days_left < 0:
        return [
            {
                "action_type": "waste",
                "subject": f"{name}: SKT geçmiş, fire olarak işle",
                "description": (
                    f"{ctx['lot_number']} lot'unun son kullanma tarihi geçti "
                    f"({qty} {ctx['unit']} stokta). Fire kaydı oluşturup "
                    f"stoktan düşmek gerekiyor."
                ),
                "suggested_discount_pct": None,
                "priority": 1,
            }
        ]

    natural_days = ctx["natural_consumption_days"]
    actions: list[dict] = []

    if days_left <= 3:
        # Acil — yüksek indirim
        pct = 40 if velocity > 0 else 50
        actions.append(
            {
                "action_type": "discount",
                "subject": f"Acil %{pct} indirim: {name}",
                "description": (
                    f"{ctx['lot_number']} lot'u sadece {days_left} gün içinde "
                    f"sona eriyor. {qty} {ctx['unit']} stokta, günde "
                    f"{velocity} satılıyor. Acil %{pct} indirim ile satışı "
                    f"hızlandırın."
                ),
                "suggested_discount_pct": pct,
                "priority": 1,
            }
        )
        if ctx["recent_buyer_count"] >= 3:
            actions.append(
                {
                    "action_type": "notify",
                    "subject": f"{name} müşterilerine bildirim gönder",
                    "description": (
                        f"Bu ürünü son dönemde {ctx['recent_buyer_count']} farklı "
                        f"müşteri aldı. Onlara özel indirim bildirimi gönderin."
                    ),
                    "suggested_discount_pct": None,
                    "priority": 1,
                }
            )
    elif days_left <= 7:
        if natural_days is None or natural_days > days_left:
            pct = 25
            actions.append(
                {
                    "action_type": "discount",
                    "subject": f"%{pct} indirim önerisi: {name}",
                    "description": (
                        f"{days_left} gün içinde SKT dolacak. {qty} "
                        f"{ctx['unit']} stok mevcut hız ile vaktinde "
                        f"tüketilemez. %{pct} indirim önerilir."
                    ),
                    "suggested_discount_pct": pct,
                    "priority": 2,
                }
            )
        actions.append(
            {
                "action_type": "delay_reorder",
                "subject": f"{name} yeni siparişini ertele",
                "description": (
                    f"Mevcut lot {days_left} gün içinde SKT'ye girecek. "
                    f"Yeni siparişi mevcut stok tüketilene kadar ertelemek "
                    f"israfı önler."
                ),
                "suggested_discount_pct": None,
                "priority": 2,
            }
        )
    else:  # 8-14 gün
        if natural_days is None or natural_days > days_left:
            pct = 15
            actions.append(
                {
                    "action_type": "bundle",
                    "subject": f"{name} ile paket teklifi oluştur",
                    "description": (
                        f"SKT 2 hafta içinde. Tamamlayıcı bir ürünle "
                        f"paket yapıp hızla tüketebilirsiniz. "
                        f"Alternatif: %{pct} indirim."
                    ),
                    "suggested_discount_pct": pct,
                    "priority": 3,
                }
            )

    return actions


async def _llm_propose_actions(ctx: dict) -> list[dict] | None:
    """Gemini'den structured JSON aksiyon listesi al. Hata olursa None."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "Sen bir KOBİ stok yönetimi danışmanısın. Aşağıdaki son kullanma "
            "tarihi yaklaşan lot için 1-3 aksiyon önerisi yaz. "
            "Türkçe konuş, Türkçe karakterleri tam kullan (ş, ç, ğ, ü, ö, ı, İ).\n\n"
            "Action tipleri:\n"
            "- discount: İndirim öner (suggested_discount_pct: 0-50)\n"
            "- bundle: Tamamlayıcı ürünle paket\n"
            "- waste: SKT geçmişse fire kaydı\n"
            "- notify: Düzenli alıcı müşterilere bildirim\n"
            "- delay_reorder: Yeni siparişi ertele\n\n"
            "Çıktıyı SADECE şu JSON formatında ver, başka hiçbir şey yazma:\n"
            "[{\"action_type\":\"discount\",\"subject\":\"...\",\"description\":\"...\","
            "\"suggested_discount_pct\":25,\"priority\":1}]\n\n"
            "priority: 1=acil, 2=normal, 3=düşük.\n"
            "subject: 60 karakter altı kısa başlık.\n"
            "description: 2-3 cümle, somut sayıları içersin.\n\n"
            f"Lot bağlamı:\n{json.dumps(ctx, ensure_ascii=False, indent=2)}"
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt
        )
        text = (response.text or "").strip()
        # Markdown code fence'i temizle
        if text.startswith("```"):
            text = text.split("```", 2)[1] if "```" in text[3:] else text
            text = text.lstrip("json").strip()
        data = json.loads(text)
        if not isinstance(data, list):
            return None
        return data
    except Exception as e:
        logger.warning("LLM action proposal failed for lot %s: %s", ctx["lot_id"], e)
        return None


async def _has_pending_actions(db: AsyncSession, lot_id: int) -> bool:
    res = await db.execute(
        select(LotAction.id)
        .where(
            LotAction.lot_id == lot_id,
            LotAction.status == LotActionStatus.PENDING,
        )
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


def _coerce_action_type(val) -> LotActionType:
    """LLM bazen 'Discount' ya da 'DISCOUNT' dönebilir; normalize et."""
    if isinstance(val, LotActionType):
        return val
    val = (val or "").lower().strip()
    try:
        return LotActionType(val)
    except ValueError:
        return LotActionType.DISCOUNT  # fallback


async def analyze_lot(
    db: AsyncSession, lot: StockLot, *, force: bool = False
) -> list[LotAction]:
    """Tek lot için öneri üret. Idempotent: pending action varsa atlanır
    (force=True ile bypass edilebilir).
    """
    if not force and await _has_pending_actions(db, lot.id):
        return []

    ctx = await _gather_lot_context(db, lot)
    actions = await _llm_propose_actions(ctx)
    if not actions:
        actions = _fallback_actions(ctx)

    created: list[LotAction] = []
    for a in actions[:3]:
        try:
            row = LotAction(
                lot_id=lot.id,
                action_type=_coerce_action_type(a.get("action_type")),
                subject=(a.get("subject") or "Öneri")[:200],
                description=(a.get("description") or "")[:1500],
                suggested_discount_pct=(
                    float(a["suggested_discount_pct"])
                    if a.get("suggested_discount_pct") is not None
                    else None
                ),
                priority=int(a.get("priority", 2)),
                status=LotActionStatus.PENDING,
            )
            db.add(row)
            created.append(row)
        except (TypeError, ValueError):
            logger.warning("Bozuk action dict atlanidi: %s", a)
            continue
    await db.flush()
    return created


async def analyze_all_expiring(
    db: AsyncSession, within_days: int = 14
) -> dict:
    """Tüm yaklaşan SKT lot'ları analiz et.

    Tek bir lot'taki LLM hatası tüm batch'i öldürmesin diye her lot ayrı
    try/except'te çalışır. Hatalı lot'lar logger.exception ile loglanır,
    sayım `lots_failed` alanında döner.
    """
    lots = await lots_crud.expiring_soon(db, within_days=within_days)
    total_actions = 0
    analyzed_lots = 0
    failed_lots = 0
    for lot in lots:
        try:
            new_actions = await analyze_lot(db, lot)
            if new_actions:
                analyzed_lots += 1
                total_actions += len(new_actions)
        except Exception as e:
            logger.exception("analyze_lot failed lot_id=%s: %s", lot.id, e)
            failed_lots += 1
    await db.commit()
    return {
        "lots_analyzed": analyzed_lots,
        "actions_created": total_actions,
        "lots_skipped": len(lots) - analyzed_lots - failed_lots,
        "lots_failed": failed_lots,
    }


async def list_actions_for_lot(
    db: AsyncSession, lot_id: int
) -> list[LotAction]:
    res = await db.execute(
        select(LotAction)
        .where(LotAction.lot_id == lot_id)
        .order_by(LotAction.priority.asc(), desc(LotAction.created_at))
    )
    return list(res.scalars())


async def list_all_pending(db: AsyncSession) -> list[LotAction]:
    res = await db.execute(
        select(LotAction)
        .where(LotAction.status == LotActionStatus.PENDING)
        .order_by(LotAction.priority.asc(), desc(LotAction.created_at))
    )
    return list(res.scalars())


async def update_status(
    db: AsyncSession, action: LotAction, new_status: LotActionStatus
) -> LotAction:
    action.status = new_status
    if new_status == LotActionStatus.APPLIED:
        action.applied_at = datetime.utcnow()
    await db.flush()
    return action
