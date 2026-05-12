import logging
from pathlib import Path

from app.core import llm as llm_core
from app.core.llm import ToolSpec
from app.db.models import Customer
from app.tools import order_tools, product_tools, shipping_tools
from app.tools.base import AgentContext

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
            name="check_product_availability",
            description="Verilen urun adi ve miktari icin stokta var mi kontrol eder.",
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
            description="Bir urunun birim fiyatini doner.",
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
    system_prompt = _PROMPT_TEMPLATE.format(
        customer_name=customer.name, customer_id=customer.id
    )
    tools = _build_tools()
    result = await llm_core.run_agent_loop(
        system_prompt=system_prompt,
        user_message=message,
        tools=tools,
        extra_context={"ctx": ctx},
    )
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
