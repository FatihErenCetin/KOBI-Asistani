import logging
from pathlib import Path

from app.core import llm as llm_core
from app.core.llm import ToolSpec
from app.db.models import Customer
from app.tools import order_tools, product_tools, shipping_tools
from app.tools.base import AgentContext

MAX_HISTORY_TURNS = 4  # Son 4 user+assistant cifti tutulur (~8 mesaj)

# In-memory conversation history: telegram_user_id -> [{"role": ..., "content": ...}]
# Uvicorn single-worker olduğu için process-local cache güvenli.
# Backend restart'ta sıfırlanır (kabul edilebilir kayıp — demo amaçlı).
_history_cache: dict[int, list[dict]] = {}


def _get_history(tg_user_id: int) -> list[dict]:
    return _history_cache.get(tg_user_id, [])


def _append_history(tg_user_id: int, user_msg: str, assistant_msg: str) -> None:
    hist = _history_cache.setdefault(tg_user_id, [])
    hist.append({"role": "user", "content": user_msg})
    hist.append({"role": "model", "content": assistant_msg})
    # Trim — son MAX_HISTORY_TURNS x 2 mesajı tut
    max_messages = MAX_HISTORY_TURNS * 2
    if len(hist) > max_messages:
        del hist[: len(hist) - max_messages]

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "customer_persona.md"
_PROMPT_TEMPLATE = PROMPT_PATH.read_text(encoding="utf-8")


def _build_tools() -> list[ToolSpec]:
    return [
        ToolSpec(
            name="get_my_order_status",
            description=(
                "Verilen siparis numarasinin durumunu ve kargo bilgisini doner. "
                "Yalniz musterinin kendi siparisi sorgulanabilir."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Siparis numarasi"}
                },
                "required": ["order_id"],
            },
            handler=order_tools.get_my_order_status,
        ),
        ToolSpec(
            name="list_my_recent_orders",
            description="Musterinin son N gundeki siparislerini listeler.",
            parameters={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Geriye dogru gun sayisi",
                    }
                },
            },
            handler=order_tools.list_my_recent_orders,
        ),
        ToolSpec(
            name="search_products",
            description=(
                "KULLAN: Musteri urun katalogu, kategori veya 'ne tur X var' "
                "tarzinda genel/listeleme sorulari sordugunda. Ornek: "
                "'hangi ballar var', 'urunler neler', 'peynir cesitleri'. "
                "Bos query ile cagirirsan tum urunleri doner."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Aranan urun adi veya kategori. Tum urunler icin bos string."
                        ),
                    },
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=product_tools.search_products,
        ),
        ToolSpec(
            name="check_product_availability",
            description=(
                "KULLAN: Kullanici BELIRLI miktarda urun istiyor ve stok var mi soruyor. "
                "Ornek: '5 kilo domates stokta var mi?'. "
                "KULLANMA: Sadece 'ne var' tarzinda genel soruda — search_products kullan."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "number"},
                },
                "required": ["name", "quantity"],
            },
            handler=product_tools.check_product_availability,
        ),
        ToolSpec(
            name="get_product_price",
            description=(
                "KULLAN: Sadece fiyat sorgusu. Ornek: 'bal ne kadar?', 'fiyat ne?'. "
                "KULLANMA: Stok da gerekiyorsa check_product_availability kullan."
            ),
            parameters={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            handler=product_tools.get_product_price,
        ),
        ToolSpec(
            name="create_order_draft",
            description=(
                "Siparis taslagi olusturur, kullaniciya onay icin sunulacak. "
                "Onaysiz siparis OLUSMAZ."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string"},
                                "quantity": {"type": "number"},
                            },
                            "required": ["product_name", "quantity"],
                        },
                    }
                },
                "required": ["items"],
            },
            handler=order_tools.create_order_draft,
        ),
        ToolSpec(
            name="get_shipment_status",
            description="Kargo takip numarasi ile kargo durumunu doner.",
            parameters={
                "type": "object",
                "properties": {"tracking_no": {"type": "string"}},
                "required": ["tracking_no"],
            },
            handler=shipping_tools.get_shipment_status,
        ),
    ]


class CustomerAgentResponse:
    def __init__(
        self,
        text: str,
        draft_id: str | None = None,
        draft_summary: dict | None = None,
    ):
        self.text = text
        self.draft_id = draft_id
        self.draft_summary = draft_summary


async def handle_message(
    *, customer: Customer, message: str, db, telegram_user_id: int
) -> CustomerAgentResponse:
    """Musteri ajaninin temel giris noktasi."""
    ctx = AgentContext(
        db=db,
        customer_id=customer.id,
        is_admin=False,
        telegram_user_id=telegram_user_id,
    )
    system_prompt = (
        _PROMPT_TEMPLATE
        .replace("{customer_name}", customer.name)
        .replace("{customer_id}", str(customer.id))
    )
    tools = _build_tools()
    history = _get_history(telegram_user_id)
    result = await llm_core.run_agent_loop(
        system_prompt=system_prompt,
        user_message=message,
        tools=tools,
        history=history,
        extra_context={"ctx": ctx},
    )
    # Bu turn'u history'e kaydet (bir sonraki mesajda context olacak)
    if result.text:
        _append_history(telegram_user_id, message, result.text)
    await db.commit()

    draft_id = None
    draft_summary = None
    for call in result.tool_calls_made:
        if call["tool"] == "create_order_draft" and "draft_id" in call.get("result", {}):
            draft_id = call["result"]["draft_id"]
            draft_summary = call["result"]
    return CustomerAgentResponse(
        text=result.text or "Bir hata oldu, tekrar dener misiniz?",
        draft_id=draft_id,
        draft_summary=draft_summary,
    )


async def handle_callback_confirm(
    *, customer: Customer, draft_id: str, db, telegram_user_id: int
) -> dict:
    ctx = AgentContext(
        db=db,
        customer_id=customer.id,
        is_admin=False,
        telegram_user_id=telegram_user_id,
    )
    result = await order_tools.confirm_order(draft_id, ctx=ctx)
    await db.commit()
    return result


async def handle_callback_cancel(
    *, customer: Customer, db, telegram_user_id: int
) -> dict:
    ctx = AgentContext(
        db=db,
        customer_id=customer.id,
        is_admin=False,
        telegram_user_id=telegram_user_id,
    )
    result = await order_tools.cancel_draft(ctx=ctx)
    await db.commit()
    return result
