from unittest.mock import AsyncMock, patch

import pytest

from app.agents import customer_agent
from app.core.llm import LLMResponse
from app.db.crud import customers as customers_crud


@pytest.mark.asyncio
async def test_handle_message_passes_customer_context(db):
    c = await customers_crud.create(db, name="Ayse", telegram_user_id=99999)
    await db.commit()

    fake = LLMResponse(text="Selam Ayse!", tool_calls_made=[])
    with patch(
        "app.agents.customer_agent.llm_core.run_agent_loop",
        new=AsyncMock(return_value=fake),
    ):
        resp = await customer_agent.handle_message(
            customer=c, message="merhaba", db=db, telegram_user_id=99999
        )
    assert resp.text == "Selam Ayse!"
    assert resp.draft_id is None


@pytest.mark.asyncio
async def test_handle_message_captures_draft(db):
    c = await customers_crud.create(db, name="Ayse", telegram_user_id=99999)
    fake = LLMResponse(
        text="Siparisinizi acmak ister misiniz?",
        tool_calls_made=[
            {
                "tool": "create_order_draft",
                "args": {},
                "result": {"draft_id": "abc123", "items": [], "total": 90},
            }
        ],
    )
    with patch(
        "app.agents.customer_agent.llm_core.run_agent_loop",
        new=AsyncMock(return_value=fake),
    ):
        resp = await customer_agent.handle_message(
            customer=c,
            message="5 kilo domates",
            db=db,
            telegram_user_id=99999,
        )
    assert resp.draft_id == "abc123"
    assert resp.draft_summary["total"] == 90
