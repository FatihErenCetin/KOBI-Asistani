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

    with patch(
        "app.core.llm.generate_content_with_fallback",
        new=AsyncMock(return_value=fake_response),
    ):
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

    handler = AsyncMock(return_value={"ok": True})
    tool = ToolSpec(
        name="get_thing",
        description="test",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        handler=handler,
    )

    with patch(
        "app.core.llm.generate_content_with_fallback",
        new=AsyncMock(side_effect=[first_response, second_response]),
    ):
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


@pytest.mark.asyncio
async def test_multi_key_fallback_on_429():
    """İlk key 429 alırsa ikinci key denenir."""
    from google.genai import errors as genai_errors

    err_429 = genai_errors.ClientError(
        code=429, response_json={"error": {"message": "rate limited"}}
    )
    ok_response = MagicMock()
    ok_response.text = "ok"

    client_a = MagicMock()
    client_a.aio.models.generate_content = AsyncMock(side_effect=err_429)
    client_b = MagicMock()
    client_b.aio.models.generate_content = AsyncMock(return_value=ok_response)

    with patch.object(llm, "_get_keys", return_value=["KEY_A", "KEY_B"]), patch.object(
        llm,
        "_client_for",
        side_effect=lambda k: client_a if k == "KEY_A" else client_b,
    ):
        res = await llm.generate_content_with_fallback(contents=["hi"])
    assert res is ok_response
    # ikinci key kullanıldı (cursor değişti)
    assert client_a.aio.models.generate_content.await_count == 1
    assert client_b.aio.models.generate_content.await_count == 1


@pytest.mark.asyncio
async def test_settings_parses_multi_keys():
    """GEMINI_API_KEYS env'i virgüllü liste olarak parse edilmeli."""
    from app.core.config import Settings

    s = Settings(GEMINI_API_KEY="primary", GEMINI_API_KEYS="k1,k2 ,k3")
    keys = s.gemini_api_keys_list
    # GEMINI_API_KEYS önce, sonra GEMINI_API_KEY (dedupe)
    assert "k1" in keys
    assert "k2" in keys
    assert "k3" in keys
    assert "primary" in keys
    assert len(keys) == 4
