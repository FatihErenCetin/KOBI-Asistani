import logging
import re
from pathlib import Path

from sqlalchemy import select

from app.core import llm as llm_core
from app.core.llm import ToolSpec
from app.db.models import Customer
from app.tools import carrier_tools, customer_tools, order_tools, product_tools
from app.tools.base import AgentContext

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "panel_persona.md"
_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


STATUS_TR = {
    "pending": "Yeni",
    "prepared": "Hazırlandı",
    "shipped": "Kargoda",
    "delivered": "Teslim edildi",
    "cancelled": "İptal edildi",
    "label_created": "Etiket oluşturuldu",
    "picked_up": "Kargoya verildi",
    "in_transit": "Transferde",
    "out_for_delivery": "Dağıtımda",
}


def _build_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="list_orders",
            description="Sistemdeki siparisleri filtreli olarak listeler.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "pending|prepared|shipped|delivered|cancelled"},
                    "since_days": {"type": "integer"},
                    "customer_id": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
            },
            handler=order_tools.list_orders,
        ),
        ToolSpec(
            name="get_order_detail",
            description="Tek siparisin tum detayini doner.",
            parameters={"type": "object", "properties": {"order_id": {"type": "integer"}}, "required": ["order_id"]},
            handler=order_tools.get_order_detail,
        ),
        ToolSpec(
            name="customer_order_history",
            description="Bir musterinin siparis gecmisini ve toplam harcamasini doner.",
            parameters={
                "type": "object",
                "properties": {"name_or_id": {"type": "string"}, "since_days": {"type": "integer"}},
                "required": ["name_or_id"],
            },
            handler=customer_tools.customer_order_history,
        ),
        ToolSpec(
            name="stock_overview",
            description="Tum stogu ya da yalniz dusuk stoklari listeler.",
            parameters={"type": "object", "properties": {"low_only": {"type": "boolean"}}},
            handler=product_tools.stock_overview,
        ),
        ToolSpec(
            name="sales_summary",
            description="Belirli gun araliginda satislari gunluk veya urun bazinda toplar.",
            parameters={
                "type": "object",
                "properties": {
                    "since_days": {"type": "integer"},
                    "group_by": {"type": "string", "description": "day veya product"},
                },
            },
            handler=order_tools.sales_summary,
        ),
        ToolSpec(
            name="top_products",
            description="Belirli gun araliginda en cok satan urunleri doner.",
            parameters={"type": "object", "properties": {"since_days": {"type": "integer"}, "limit": {"type": "integer"}}},
            handler=order_tools.top_products,
        ),
        ToolSpec(
            name="carrier_performance",
            description="Kargo firmalarinin performans analizini doner.",
            parameters={"type": "object", "properties": {"since_days": {"type": "integer"}}},
            handler=carrier_tools.carrier_performance_analysis,
        ),
        ToolSpec(
            name="at_risk_shipments",
            description="Musteri sikayet riski en yuksek siparisleri doner.",
            parameters={"type": "object", "properties": {}},
            handler=carrier_tools.high_complaint_risk_orders,
        ),
    ]


class PanelAgentResponse:
    def __init__(self, text: str, data: dict | None):
        self.text = text
        self.data = data


def _normalize(text: str) -> str:
    replacements = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    })
    return text.translate(replacements).lower()


def _money(value: float | int | None) -> str:
    amount = float(value or 0)
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"₺{formatted}"


def _status(value: str | None) -> str:
    return STATUS_TR.get(value or "", value or "-")


def _order_text(result: dict) -> str:
    orders = result.get("orders") or []
    if not orders:
        return "Bu filtreye uygun sipariş bulunamadı."
    return f"{len(orders)} sipariş listelendi. Öncelik sırası tarihe göre hazırlandı."


async def _detect_customer_name(message: str, ctx: AgentContext) -> str | None:
    q = _normalize(message)
    res = await ctx.db.execute(select(Customer.name))
    names = list(res.scalars())
    for name in names:
        n = _normalize(name)
        parts = [p for p in n.split() if len(p) > 1]
        if n in q or (parts and all(p in q for p in parts)):
            return name
    return None


def _period_days(q: str) -> int:
    if any(w in q for w in ("bugun", "bugün", "24 saat")):
        return 1
    if any(w in q for w in ("ay", "30")):
        return 30
    if any(w in q for w in ("hafta", "7")):
        return 7
    return 7


def _operation_summary_payload(pending: dict, low: dict, risks: dict) -> dict:
    low_products = low.get("products", [])[:3]
    risk_orders = risks.get("orders", [])[:3]
    pending_orders = pending.get("orders", [])[:3]
    cards = [
        {
            "title": "Hazırlanacak sipariş",
            "value": pending.get("count", 0),
            "tone": "amber",
            "description": "Yeni siparişler paketleme sırasına alınmalı.",
        },
        {
            "title": "Kritik stok",
            "value": low.get("count", 0),
            "tone": "rose" if low.get("count", 0) else "emerald",
            "description": "Eşik altındaki ürünler tedarik planına alınmalı.",
        },
        {
            "title": "Kargo riski",
            "value": risks.get("count", 0),
            "tone": "rose" if risks.get("count", 0) else "emerald",
            "description": "Gecikmiş gönderiler müşteri memnuniyetini etkileyebilir.",
        },
    ]
    actions = []
    if low_products:
        p = low_products[0]
        actions.append(f"{p['name']} için yaklaşık {p.get('suggested_reorder_qty', p.get('low_stock_threshold', 0))} {p.get('unit', '')} tedarik planı oluştur.")
    if risk_orders:
        r = risk_orders[0]
        actions.append(f"#{r['order_id']} numaralı geciken kargo için müşteriye bilgilendirme mesajı gönder.")
    if pending_orders:
        actions.append("Bekleyen siparişleri paketleme önceliğine göre sırala.")
    return {"type": "operation_summary", "cards": cards, "actions": actions}


async def _stock_response(ctx: AgentContext, low_only: bool) -> PanelAgentResponse:
    result = await product_tools.stock_overview(low_only=low_only, ctx=ctx)
    if "error" in result:
        return PanelAgentResponse(result["error"], data=None)
    products = result.get("products", [])
    if not products:
        text = "Kritik stokta ürün görünmüyor. Stok seviyesi şu an güvenli."
    elif low_only:
        first = products[0]
        text = (
            f"{len(products)} kritik stok ürünü var. En acil ürün {first['name']}: "
            f"{first['stock']} {first['unit']} kaldı. Önerilen tedarik: "
            f"{first.get('suggested_reorder_qty', first.get('low_stock_threshold', 0))} {first['unit']}."
        )
    else:
        text = f"{len(products)} ürünün stok özeti hazır. Kritik ürünler üstte gösterildi."
    return PanelAgentResponse(text, data={"type": "stock_overview", **result})


async def _deterministic_response(message: str, ctx: AgentContext) -> PanelAgentResponse | None:
    """Demo icin guvenli intent yakalama.

    Bilinen panel sorularinda LLM'e gitmeden dogrudan veriyi sorgular.
    Boylece kota, rate limit veya yanlis tool secimi yuzunden demo bozulmaz.
    """
    q = _normalize(message)

    # Aksiyon: kritik stok icin tedarikci mesaj taslagi.
    if any(w in q for w in ("tedarik", "siparis ver", "sipariş ver", "satinal", "satın al")) and any(w in q for w in ("mesaj", "mail", "taslak", "hazirla", "hazırla", "stok", "urun", "ürün")):
        result = await product_tools.stock_overview(low_only=True, ctx=ctx)
        products = result.get("products", [])
        if not products:
            return PanelAgentResponse("Tedarik mesajı gerektiren kritik stok ürünü görünmüyor.", data=None)
        lines = []
        for p in products[:4]:
            qty = p.get("suggested_reorder_qty", p.get("low_stock_threshold", 0))
            lines.append(f"{p['name']}: {qty} {p['unit']}")
        draft = "Merhaba, aşağıdaki ürünler için tedarik planlamak istiyoruz:\n" + "\n".join(lines) + "\n\nUygunluk, birim fiyat ve tahmini teslim süresi bilgisini paylaşabilir misiniz?"
        subject = "Kritik Stok Tedarik Talebi"
        return PanelAgentResponse(
            "Kritik stoklar için tedarikçi mail taslağı hazır. Kontrol edip onaylarsanız Gmail üzerinden gönderirim.",
            data={
                "type": "action_suggestion",
                "action": "supplier_email",
                "title": "Tedarikçi mail taslağı",
                "description": "Onayladığınızda .env içindeki SUPPLIER_EMAIL adresine Gmail ile gönderilir.",
                "subject": subject,
                "body": draft,
                "primaryActionLabel": "Onayla ve mail gönder",
            },
        )

    # Aksiyon: geciken kargo icin musteri mesaj taslagi.
    if any(w in q for w in ("kargo", "gecik", "teslimat", "risk")) and any(w in q for w in ("mesaj", "bilgilendir", "taslak", "hazirla", "hazırla")):
        result = await carrier_tools.high_complaint_risk_orders(ctx=ctx)
        risks = result.get("orders", [])
        if not risks:
            return PanelAgentResponse("Müşteriye mesaj gerektiren gecikmiş kargo kaydı bulunmadı.", data=None)
        r = risks[0]
        draft = (
            f"Merhaba {r.get('customer', '')}, #{r.get('order_id')} numaralı siparişinizin teslimatında kısa bir gecikme görünüyor. "
            f"Kargo firmasıyla süreci takip ediyoruz. Güncel konum: {r.get('location', '-')}. "
            "Yeni bilgi geldikçe sizi bilgilendireceğiz. Anlayışınız için teşekkür ederiz."
        )
        return PanelAgentResponse("Geciken kargo için müşteri bilgilendirme taslağı hazır.", data={"type": "action_suggestion", "title": "Müşteri bilgilendirme taslağı", "body": draft})

    # 1) Siparis numarasi sorgusu: "128 numarali siparis nerede?"
    if any(w in q for w in ("siparis", "sipariş", "order")):
        match = re.search(r"#?\b(\d{2,})\b", q)
        if match:
            result = await order_tools.get_order_detail(order_id=int(match.group(1)), ctx=ctx)
            if "error" in result:
                return PanelAgentResponse(result["error"], data=None)
            shipment = result.get("shipment") or {}
            items = result.get("items") or []
            item_text = ", ".join([f"{it.get('product')} ({it.get('quantity')})" for it in items[:3]]) or "Ürün detayı yok"
            if shipment:
                text = (
                    f"#{result['order_id']} siparişi {result.get('customer_name', '-') } adına kayıtlı. "
                    f"Sipariş durumu: {_status(result.get('status'))}. Kargo: {shipment.get('carrier', '-')}, "
                    f"gönderi durumu: {_status(shipment.get('status'))}, son konum: {shipment.get('location', '-')}. "
                    f"Tahmini teslim: {shipment.get('eta', '-')}. Ürünler: {item_text}."
                )
            else:
                text = f"#{result['order_id']} siparişi bulundu. Durum: {_status(result.get('status'))}. Ürünler: {item_text}."
            return PanelAgentResponse(text, data={"type": "order_list", "orders": [result], "count": 1})

    # 2) Musteri bazli siparis gecmisi: "Ayse Yilmaz'in son siparisleri"
    if any(w in q for w in ("musteri", "müşteri", "son siparis", "son sipariş", "siparislerini", "siparişlerini", "siparisleri", "siparişleri")):
        customer_name = await _detect_customer_name(message, ctx)
        if customer_name:
            result = await customer_tools.customer_order_history(name_or_id=customer_name, since_days=90, ctx=ctx)
            if "error" in result:
                return PanelAgentResponse(result["error"], data=None)
            orders = result.get("orders", [])
            total = result.get("total_spend", 0)
            latest = orders[0] if orders else None
            if latest:
                text = (
                    f"{customer_name} için son {len(orders)} sipariş listelendi. "
                    f"Toplam harcama: {_money(total)}. En son sipariş #{latest['order_id']} ve durumu {_status(latest.get('status'))}."
                )
            else:
                text = f"{customer_name} için son 90 günde sipariş bulunamadı."
            return PanelAgentResponse(text, data={"type": "order_list", "orders": orders, "count": len(orders)})

    # 3) Bekleyen/acil siparisler
    if any(w in q for w in ("bekleyen", "acil", "yeni", "hazirlanacak", "hazırlanacak")) and any(w in q for w in ("siparis", "sipariş")):
        result = await order_tools.list_orders(status="pending", since_days=14, limit=10, ctx=ctx)
        orders = result.get("orders", [])
        if orders:
            first = orders[0]
            text = (
                f"{len(orders)} bekleyen sipariş listelendi. İlk öncelik #{first['order_id']} "
                f"({first.get('customer_name', '-')}, {_money(first.get('total'))})."
            )
        else:
            text = "Son 14 günde bekleyen acil sipariş görünmüyor."
        return PanelAgentResponse(text, data={"type": "order_list", **result})

    # 4) Satis/grafik niyeti: "Bu hafta gunluk satis grafigi"
    if any(w in q for w in ("satis", "satış", "ciro", "gelir", "revenue", "grafik")):
        since_days = _period_days(q)
        group_by = "product" if any(w in q for w in ("urun", "ürün", "kategori", "en cok", "en çok")) else "day"
        result = await order_tools.sales_summary(since_days=since_days, group_by=group_by, ctx=ctx)
        if "error" in result:
            return PanelAgentResponse(result["error"], data=None)
        rows = result.get("rows", [])
        total = result.get("total_revenue")
        if group_by == "day":
            text = f"Son {since_days} gün için günlük satış grafiği hazır. Toplam ciro: {_money(total)}."
        else:
            best = rows[0] if rows else None
            text = f"Son {since_days} gün için ürün bazlı satış özeti hazır. En güçlü ürün: {best['product']}." if best else f"Son {since_days} gün için ürün bazlı satış bulunamadı."
        return PanelAgentResponse(text, data={"type": "sales_summary", **result})

    # 5) Stok/envanter niyeti
    if any(w in q for w in ("stok", "stock", "envanter", "urun", "ürün")):
        low_only = any(w in q for w in ("dusuk", "düşük", "kritik", "az", "bit", "low"))
        return await _stock_response(ctx, low_only=low_only)

    # 6) Kargo/teslimat niyeti
    if any(w in q for w in ("kargo", "cargo", "carrier", "teslimat", "gecik", "geciken", "risk")):
        if any(w in q for w in ("risk", "geciken", "sikayet", "şikayet", "problem", "sorun")):
            result = await carrier_tools.high_complaint_risk_orders(ctx=ctx)
            count = result.get("count", 0)
            if count:
                first = result.get("orders", [])[0]
                text = f"Şikayet riski yüksek {count} kargo kaydı var. En acil kayıt #{first['order_id']}, {first.get('days_late', 0)} gün gecikmiş."
            else:
                text = "Şikayet riski yüksek kargo kaydı bulunmadı."
            return PanelAgentResponse(text, data={"type": "carrier_risks", **result})
        result = await carrier_tools.carrier_performance_analysis(since_days=30, ctx=ctx)
        text = f"Son 30 günlük kargo analizi hazır. Genel gecikme oranı %{result.get('overall_delay_rate_pct', 0)}."
        return PanelAgentResponse(text, data={"type": "carrier_analysis", **result})

    # 7) Genel operasyon ozeti
    if any(w in q for w in ("operasyon", "ozet", "özet", "dashboard", "bugun", "bugün")):
        pending = await order_tools.list_orders(status="pending", since_days=14, limit=10, ctx=ctx)
        low = await product_tools.stock_overview(low_only=True, ctx=ctx)
        risks = await carrier_tools.high_complaint_risk_orders(ctx=ctx)
        actions = _operation_summary_payload(pending, low, risks)
        text = (
            f"Operasyon özeti hazır: {pending.get('count', 0)} bekleyen sipariş, "
            f"{low.get('count', 0)} kritik stok ürünü ve "
            f"{risks.get('count', 0)} yüksek riskli kargo kaydı görünüyor. "
            "Önerilen aksiyonları aşağıya ekledim."
        )
        return PanelAgentResponse(text, data=actions)

    return None


def _infer_render_type(tool_calls: list[dict]) -> dict | None:
    if not tool_calls:
        return None
    last = tool_calls[-1]
    name = last["tool"]
    result = last.get("result", {})
    if "error" in result:
        return None
    if name == "customer_order_history":
        return {"type": "order_list", "orders": result.get("orders", []), "count": result.get("order_count", 0)}
    if name in ("list_orders", "get_order_detail"):
        if name == "get_order_detail":
            return {"type": "order_list", "orders": [result], "count": 1}
        return {"type": "order_list", **result}
    if name == "stock_overview":
        return {"type": "stock_overview", **result}
    if name in ("sales_summary", "top_products"):
        return {"type": "sales_summary", **result}
    if name == "carrier_performance":
        return {"type": "carrier_analysis", **result}
    if name == "at_risk_shipments":
        return {"type": "carrier_risks", **result}
    return {"type": "raw", **result}


async def handle(message: str, *, db, history: list[dict] | None = None) -> PanelAgentResponse:
    ctx = AgentContext(db=db, is_admin=True)

    deterministic = await _deterministic_response(message, ctx)
    if deterministic is not None:
        await db.commit()
        return deterministic

    try:
        result = await llm_core.run_agent_loop(
            system_prompt=_PROMPT,
            user_message=message,
            tools=_build_tools(),
            history=history,
            extra_context={"ctx": ctx},
        )
        await db.commit()
        return PanelAgentResponse(
            text=result.text or "Bu sorgu için sonuç bulamadım.",
            data=_infer_render_type(result.tool_calls_made),
        )
    except Exception as exc:
        is_rate_limit = (
            getattr(exc, "code", None) == 429
            or "429" in str(exc)
            or "RESOURCE_EXHAUSTED" in str(exc)
        )
        if not is_rate_limit:
            raise

        logger.warning("Gemini rate limit nedeniyle lokal fallback çalıştı.")
        fallback = await _deterministic_response(message, ctx)
        await db.commit()
        if fallback is not None:
            return fallback
        return PanelAgentResponse(
            text="AI kotası dolu. Demo için sipariş, stok, satış veya kargo sorgusu yazabilirsiniz.",
            data=None,
        )
