from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core import llm
from app.core.llm import LLMResponse, ToolSpec


@pytest.mark.asyncio
async def test_run_agent_loop_no_tool_calls():
    """Gemini sadece text donerse direkt cevap."""
    fake_response = MagicMock()
    fake_response.function_calls = []
    fake_response.text = "Merhaba!"
    fake_response.candidates = [MagicMock(content=MagicMock(parts=[]))]

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(return_value=fake_response)

    with patch("app.core.llm._get_client", return_value=fake_client):
        result = await llm.run_agent_loop(
            system_prompt="test",
            user_message="merhaba",
            tools=[],
        )
    assert result.text == "Merhaba!"
    assert result.tool_calls_made == []


@pytest.mark.asyncio
async def test_run_agent_loop_invokes_tool_then_text():
    """Gemini once tool cagrisi yapar, sonra final text doner."""
    fake_call = MagicMock()
    fake_call.name = "get_thing"
    fake_call.args = {"x": 1}

    first_response = MagicMock()
    first_response.function_calls = [fake_call]
    first_response.candidates = [MagicMock(content=MagicMock(role="model", parts=[]))]
    first_response.text = ""

    second_response = MagicMock()
    second_response.function_calls = []
    second_response.text = "Iste cevap"
    second_response.candidates = [MagicMock(content=MagicMock(parts=[]))]

    fake_client = MagicMock()
    fake_client.aio.models.generate_content = AsyncMock(side_effect=[first_response, second_response])

    handler = AsyncMock(return_value={"ok": True})
    tool = ToolSpec(
        name="get_thing",
        description="test",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        handler=handler,
    )

    with patch("app.core.llm._get_client", return_value=fake_client):
        result: LLMResponse = await llm.run_agent_loop(
            system_prompt="test",
            user_message="get thing",
            tools=[tool],
        )

    assert result.text == "Iste cevap"
    assert len(result.tool_calls_made) == 1
    assert result.tool_calls_made[0]["tool"] == "get_thing"
    assert result.tool_calls_made[0]["result"] == {"ok": True}
    handler.assert_awaited_once_with(x=1)
