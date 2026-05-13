import logging
from pathlib import Path

from app.core import llm as llm_core
from app.core.llm import ToolSpec
from app.tools import analytics_tools, customer_tools, order_tools, product_tools
from app.tools.base import AgentContext

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "panel_persona.md"
_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


def _build_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="list_orders",
            description="Sistemdeki siparisleri filtreli olarak listeler.",
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "pending|prepared|shipped|delivered|cancelled",
                    },
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
            parameters={
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            },
            handler=order_tools.get_order_detail,
        ),
        ToolSpec(
            name="customer_order_history",
            description=(
                "Bir musterinin siparis gecmisini ve toplam harcamasini doner. "
                "name_or_id parametresi musteri adi (string, ornegin 'Ayse') veya id (sayi) olabilir."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name_or_id": {"type": "string"},
                    "since_days": {"type": "integer"},
                },
                "required": ["name_or_id"],
            },
            handler=customer_tools.customer_order_history,
        ),
        ToolSpec(
            name="stock_overview",
            description="Tum stogu ya da yalniz dusuk stoklari listeler.",
            parameters={
                "type": "object",
                "properties": {"low_only": {"type": "boolean"}},
            },
            handler=product_tools.stock_overview,
        ),
        ToolSpec(
            name="sales_summary",
            description=(
                "Belirli gun araliginda satislari gunluk veya urun bazinda toplar. "
                "group_by 'day' veya 'product' olabilir."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "since_days": {"type": "integer"},
                    "group_by": {
                        "type": "string",
                        "description": "day veya product",
                    },
                },
            },
            handler=order_tools.sales_summary,
        ),
        ToolSpec(
            name="top_products",
            description="Belirli gun araliginda en cok satan urunleri doner.",
            parameters={
                "type": "object",
                "properties": {
                    "since_days": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
            },
            handler=order_tools.top_products,
        ),
        ToolSpec(
            name="low_margin_products",
            description=(
                "Kar marji belirli yuzdenin altinda olan urunleri listeler. "
                "Marj = (satis_fiyati - maliyet) / satis_fiyati * 100. "
                "Varsayilan esik %20. Kullanim ornekleri: 'karli olmayan urunler', "
                "'marji dusuk olanlar', 'hangi urunlerden kazanmiyorum'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "margin_threshold": {
                        "type": "number",
                        "description": "Yuzde olarak esik, varsayilan 20",
                    }
                },
            },
            handler=analytics_tools.low_margin_products,
        ),
        ToolSpec(
            name="fast_depleting",
            description=(
                "Mevcut satis hiziyla N gun icinde bitecek urunleri listeler. "
                "Varsayilan 7 gun. Kullanim: 'tukenmek uzere olanlar', "
                "'yakinda bitecek', 'stogu azalan urunler'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "max_days": {
                        "type": "number",
                        "description": "Gun esigi, varsayilan 7",
                    }
                },
            },
            handler=analytics_tools.fast_depleting,
        ),
        ToolSpec(
            name="supplier_performance",
            description=(
                "Her tedarikci icin ortalama tedarik suresi (lead time), bagli urun "
                "sayisi ve son alis tarihini gosterir. Kullanim: 'tedarikciler nasil', "
                "'lead time', 'hangi tedarikci hizli'."
            ),
            parameters={"type": "object", "properties": {}},
            handler=analytics_tools.supplier_performance,
        ),
        ToolSpec(
            name="product_analytics_report",
            description=(
                "Tek bir urun icin 30 gunluk satis adedi, ciro, gunluk hiz, "
                "kac gunluk stok kaldigi, kar marji ozeti. Bir urun adi gectigi her "
                "yerde tek urun bilgisi icin kullan."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Urun id'si",
                    }
                },
                "required": ["product_id"],
            },
            handler=analytics_tools.product_analytics_report,
        ),
        ToolSpec(
            name="category_stock",
            description=(
                "Kategori bazinda urun sayisi, toplam stok ve dusuk stok sayisini "
                "doner. Kullanim: 'hangi kategoride az stok var', "
                "'kategori bazli stok dagilim'."
            ),
            parameters={"type": "object", "properties": {}},
            handler=analytics_tools.category_stock,
        ),
    ]


class PanelAgentResponse:
    def __init__(self, text: str, data: dict | None):
        self.text = text
        self.data = data


def _infer_render_type(tool_calls: list[dict]) -> dict | None:
    """LLM tool sonuclarindan frontend render tipini cikar."""
    if not tool_calls:
        return None
    last = tool_calls[-1]
    name = last["tool"]
    result = last.get("result", {})
    if "error" in result:
        return None
    if name in ("list_orders", "get_order_detail", "customer_order_history"):
        return {"type": "order_list", **result}
    if name == "stock_overview":
        return {"type": "stock_overview", **result}
    if name in ("sales_summary", "top_products"):
        return {"type": "sales_summary", **result}
    if name == "low_margin_products":
        return {"type": "low_margin", **result}
    if name == "fast_depleting":
        return {"type": "fast_depleting", **result}
    if name == "supplier_performance":
        return {"type": "supplier_performance", **result}
    if name == "product_analytics_report":
        return {"type": "product_analytics", **result}
    if name == "category_stock":
        return {"type": "category_stock", **result}
    return {"type": "raw", **result}


async def handle(
    message: str, *, db, history: list[dict] | None = None
) -> PanelAgentResponse:
    ctx = AgentContext(db=db, is_admin=True)
    result = await llm_core.run_agent_loop(
        system_prompt=_PROMPT,
        user_message=message,
        tools=_build_tools(),
        history=history,
        extra_context={"ctx": ctx},
    )
    await db.commit()
    return PanelAgentResponse(
        text=result.text or "Bu sorgu icin sonuc bulamadim.",
        data=_infer_render_type(result.tool_calls_made),
    )
