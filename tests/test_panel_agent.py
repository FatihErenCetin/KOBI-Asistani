from unittest.mock import AsyncMock, patch

import pytest

from app.agents import panel_agent
from app.core.llm import LLMResponse


@pytest.mark.asyncio
async def test_handle_with_sales_summary(db):
    fake = LLMResponse(
        text="Bu hafta 12 siparis, 3450 TL gelir.",
        tool_calls_made=[
            {
                "tool": "sales_summary",
                "args": {"since_days": 7, "group_by": "day"},
                "result": {
                    "group_by": "day",
                    "rows": [{"day": "2026-05-12", "revenue": 3450, "order_count": 12}],
                    "total_revenue": 3450,
                },
            }
        ],
    )
    with patch(
        "app.agents.panel_agent.llm_core.run_agent_loop",
        new=AsyncMock(return_value=fake),
    ):
        resp = await panel_agent.handle("bu hafta satis", db=db)
    assert resp.data["type"] == "sales_summary"
    assert resp.data["total_revenue"] == 3450
