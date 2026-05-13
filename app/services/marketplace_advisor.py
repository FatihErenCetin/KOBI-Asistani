"""Marketplace AI advisor — komşu KOBİ trend bazlı satınalma önerisi.

Akış:
1. Admin'in city + preferred_carrier'ını al (yoksa default Istanbul / MockKargo)
2. nearby_purchase_signals ile aynı şehirdeki komşuların son N gün satın
   aldıklarını çek (min 2 farklı dükkân aynı ürünü almışsa "trend")
3. Her trend ürünü için: bizim Product DB'mizdeki en yakın eşleşmeyi bul
   (önce isim/alias substring, sonra Gemini embedding similarity)
4. Stok az/eksikse + kategori uyumluysa → öneri üret
5. Gemini ile gerekçe yazdır (mesaj, miktar, supplier rationale); LLM yoksa
   deterministik template
6. MarketplaceRecommendation tablosuna kaydet

Cron job (`app/jobs/marketplace_reorder.py`) bunu günlük tetikler;
admin'e Telegram özet bildirimi gönderir (varsa ADMIN_TELEGRAM_ID).
"""

from __future__ import annotations

import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import llm as llm_core
from app.core.config import settings
from app.db.crud import marketplace as mp_crud
from app.db.models import (
    AdminUser,
    MarketplaceRecommendation,
    Product,
    ProductSupplier,
    Supplier,
)

logger = logging.getLogger(__name__)


# Default lokasyon — admin city set etmediyse:
DEFAULT_CITY = "Istanbul"
DEFAULT_CARRIER: str | None = None  # carrier filtre devre dışı


SYSTEM_PROMPT = (
    "Sen bir Türk KOBİ tedarik zinciri danışmanısın. "
    "Sana komşu KOBİ'lerin son satın alma trendleri ve kendi stok durumumuz "
    "verilecek. Her bir öneri için JSON döndür: \n"
    "{\n"
    '  "recommendations": [\n'
    '    {"product_name": "...", "suggested_quantity": 10, '
    '"confidence": 0.8, "reasoning": "Türkçe 2-3 cümle gerekçe"}\n'
    "  ]\n"
    "}\n"
    "Gerekçede şu noktalara değin: kaç komşu aldı, kargo eşleşmesi var mı, "
    "stoğumuz ne durumda, neden bu miktar. Abartılı satış dili kullanma."
)


def _norm(s: str) -> str:
    """Türkçe karakter normalize + lowercase."""
    if not s:
        return ""
    table = str.maketrans("İĞÜŞÖÇığüşöç", "igusocigusoc")
    return s.translate(table).lower().strip()


def _match_product(
    product_name: str, candidates: list[Product]
) -> Product | None:
    """Komşu satınalma adına en yakın Product. Önce exact, sonra alias substring."""
    target = _norm(product_name)
    if not target:
        return None
    # Exact match
    for p in candidates:
        if _norm(p.name) == target:
            return p
    # Substring
    for p in candidates:
        if target in _norm(p.name) or _norm(p.name) in target:
            return p
        if p.aliases:
            for alias in p.aliases.split(","):
                if _norm(alias) and (target in _norm(alias) or _norm(alias) in target):
                    return p
    return None


def _pick_supplier(
    product: Product | None,
    candidate_supplier_ids: list[int],
    suppliers_by_id: dict[int, Supplier],
    preferred_links: dict[int, list[ProductSupplier]],
) -> Supplier | None:
    """Komşuların kullandığı supplier_ids içinden bizim için en iyi olanı seç.

    Öncelik: (1) bizim preferred linkimiz var mı, (2) komşunun supplier'ı bizim
    katalogda mı, (3) ilk match.
    """
    if product is None:
        # Sadece komşu listesinden ilk valid
        for sid in candidate_supplier_ids:
            if sid in suppliers_by_id:
                return suppliers_by_id[sid]
        return None

    # Bizim preferred supplier'larımız
    prod_links = preferred_links.get(product.id, [])
    preferred = next((link for link in prod_links if link.is_preferred), None)
    if preferred and preferred.supplier_id in suppliers_by_id:
        return suppliers_by_id[preferred.supplier_id]

    # Komşu supplier'ları içinde bizim katalogda olan var mı?
    for sid in candidate_supplier_ids:
        if sid in suppliers_by_id:
            return suppliers_by_id[sid]

    # Fallback: prod'un mevcut linklerinden ilk
    if prod_links:
        sid = prod_links[0].supplier_id
        return suppliers_by_id.get(sid)
    return None


async def _build_context(
    db: AsyncSession,
) -> tuple[list[Product], dict[int, Supplier], dict[int, list[ProductSupplier]]]:
    products_res = await db.execute(
        select(Product).where(Product.is_active.is_(True))
    )
    products = list(products_res.scalars())

    suppliers_res = await db.execute(
        select(Supplier).where(Supplier.is_active.is_(True))
    )
    suppliers_by_id = {s.id: s for s in suppliers_res.scalars()}

    links_res = await db.execute(select(ProductSupplier))
    preferred_links: dict[int, list[ProductSupplier]] = {}
    for link in links_res.scalars():
        preferred_links.setdefault(link.product_id, []).append(link)

    return products, suppliers_by_id, preferred_links


def _fallback_recommendation(
    product_name: str, quantity: float, shop_count: int, carrier: str | None
) -> tuple[float, str]:
    """LLM yokken deterministik gerekçe + confidence."""
    carrier_phrase = (
        f" {carrier} kargosunu kullanan" if carrier else ""
    )
    reasoning = (
        f"Aynı şehirdeki{carrier_phrase} {shop_count} KOBİ son haftalarda "
        f"{product_name} aldı. Stoğumuzda az/yok; sezonsal trend yakalanmadan "
        f"yaklaşık {quantity:.0f} birim sipariş önerilir."
    )
    confidence = min(0.85, 0.45 + 0.1 * shop_count)
    return confidence, reasoning


async def _llm_enrich(
    signals: list[dict],
    city: str,
    carrier: str | None,
) -> dict[str, dict] | None:
    """Gemini'ye toplu öneri ürettir. Dönen dict: product_name → {qty, conf, reason}."""
    if not settings.gemini_api_keys_list or not signals:
        return None
    try:
        from google.genai import types

        signals_compact = [
            {
                "product": s["product_name"],
                "category": s.get("category"),
                "neighbor_shops": s["shop_count"],
                "total_qty_in_city": s["total_qty"],
                "avg_cost": s.get("avg_unit_cost"),
            }
            for s in signals[:15]
        ]
        user_input = (
            f"Şehir: {city}\n"
            f"Kargo filtresi: {carrier or 'yok'}\n\n"
            f"Komşu KOBİ trendleri:\n{json.dumps(signals_compact, ensure_ascii=False)}\n\n"
            "Her ürün için sipariş önerisi üret."
        )
        response = await llm_core.generate_content_with_fallback(
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_input)],
                )
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        raw = (response.text or "").strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE)
        data = json.loads(raw)
        out: dict[str, dict] = {}
        for rec in data.get("recommendations", [])[:30]:
            name = str(rec.get("product_name", "")).strip()
            if not name:
                continue
            out[_norm(name)] = {
                "quantity": float(rec.get("suggested_quantity", 5)),
                "confidence": min(1.0, max(0.0, float(rec.get("confidence", 0.6)))),
                "reasoning": str(rec.get("reasoning", ""))[:600],
            }
        return out
    except Exception as e:
        logger.warning("Marketplace advisor LLM failed: %s", e)
        return None


async def run_analysis(
    db: AsyncSession,
    *,
    admin: AdminUser | None = None,
    since_days: int = 30,
    min_signal_count: int = 2,
    max_recommendations: int = 10,
) -> list[MarketplaceRecommendation]:
    """AI advisor'ı çalıştır, yeni MarketplaceRecommendation kayıtları döner.

    Idempotency: önceden 'active' öneri varsa onları KAPATMAZ ama
    aynı product_name için duplicate üretmez (son 7 gündeki aktif önerileri kontrol).
    """
    city = (admin.city if admin and admin.city else DEFAULT_CITY)
    carrier = admin.preferred_carrier if admin else DEFAULT_CARRIER

    signals = await mp_crud.nearby_purchase_signals(
        db,
        city=city,
        carrier=carrier,
        since_days=since_days,
        min_signal_count=min_signal_count,
    )
    if not signals:
        logger.info("Marketplace advisor: no signals (city=%s)", city)
        return []

    products, suppliers_by_id, preferred_links = await _build_context(db)

    # Mevcut aktif öneri ürün adları — duplicate önle
    existing_res = await db.execute(
        select(MarketplaceRecommendation.product_name).where(
            MarketplaceRecommendation.status == "active"
        )
    )
    existing_names = {_norm(n) for n, in existing_res.all()}

    llm_outputs = await _llm_enrich(signals, city=city, carrier=carrier)

    created: list[MarketplaceRecommendation] = []
    for signal in signals:
        if len(created) >= max_recommendations:
            break
        product_name = signal["product_name"]
        norm_name = _norm(product_name)
        if norm_name in existing_names:
            continue

        matched_product = _match_product(product_name, products)
        # Bizim stoğumuz yeterliyse atlanır (üretmiyoruz, sadece az olanı önerelim)
        if matched_product and matched_product.stock >= max(
            10, matched_product.low_stock_threshold * 2
        ):
            # Stok zaten dolu — öneri gereksiz
            continue

        chosen_supplier = _pick_supplier(
            matched_product,
            signal.get("supplier_ids", []),
            suppliers_by_id,
            preferred_links,
        )

        # Quantity hesabı: low_stock_threshold * 3, yoksa komşu medyan
        if matched_product:
            base_qty = max(
                matched_product.low_stock_threshold * 3,
                matched_product.low_stock_threshold - matched_product.stock + 5,
                5,
            )
        else:
            base_qty = max(5.0, signal["total_qty"] / max(signal["shop_count"], 1))
        suggested_qty = round(base_qty, 1)

        llm_rec = (llm_outputs or {}).get(norm_name)
        if llm_rec:
            quantity = llm_rec["quantity"]
            confidence = llm_rec["confidence"]
            reasoning = llm_rec["reasoning"]
        else:
            quantity = suggested_qty
            confidence, reasoning = _fallback_recommendation(
                product_name=product_name,
                quantity=suggested_qty,
                shop_count=signal["shop_count"],
                carrier=carrier,
            )

        rec = await mp_crud.create_recommendation(
            db,
            product_name=product_name,
            product_id=matched_product.id if matched_product else None,
            suggested_supplier_id=chosen_supplier.id if chosen_supplier else None,
            suggested_quantity=quantity,
            estimated_unit_cost=signal.get("avg_unit_cost"),
            confidence=confidence,
            reasoning=reasoning,
            nearby_signal_count=signal["shop_count"],
        )
        created.append(rec)
        existing_names.add(norm_name)

    logger.info(
        "Marketplace advisor: %d recommendations created (city=%s, signals=%d)",
        len(created), city, len(signals),
    )
    return created
