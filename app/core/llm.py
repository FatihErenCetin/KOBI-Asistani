"""Gemini function calling wrapper (google-genai SDK).

Tool seti dis taraftan Python fonksiyonlari + ToolSpec seklinde gecirilir.
LLM dongusu max 5 iterasyon ile sinirli."""

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5
RATE_LIMIT_MAX_RETRIES = 3
RATE_LIMIT_DEFAULT_WAIT = 12  # saniye, retry_delay parse edilemezse


async def _generate_with_retry(client, *, model, contents, config):
    """429 RESOURCE_EXHAUSTED yakalanirsa belirtilen sure kadar bekle ve tekrar dene."""
    for attempt in range(RATE_LIMIT_MAX_RETRIES):
        try:
            return await client.aio.models.generate_content(
                model=model, contents=contents, config=config
            )
        except genai_errors.ClientError as e:
            if getattr(e, "code", None) != 429:
                raise
            wait_s = RATE_LIMIT_DEFAULT_WAIT
            msg = str(e)
            m = re.search(r"'?retryDelay'?\s*:\s*'?(\d+)", msg)
            if m:
                wait_s = min(int(m.group(1)) + 1, 60)
            logger.warning(
                "Gemini 429, attempt %d/%d, waiting %ds",
                attempt + 1, RATE_LIMIT_MAX_RETRIES, wait_s,
            )
            await asyncio.sleep(wait_s)
    # Tum retry'lar tukendi - bir kez daha dene, bu sefer hata propagate olsun
    return await client.aio.models.generate_content(
        model=model, contents=contents, config=config
    )


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict  # JSON-schema-like dict
    handler: Callable[..., Awaitable[dict]]


@dataclass
class LLMResponse:
    text: str
    tool_calls_made: list[dict]


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _dict_to_schema(d: dict) -> types.Schema:
    """JSON-schema benzeri dict -> types.Schema donusumu."""
    type_map = {
        "string": "STRING",
        "integer": "INTEGER",
        "number": "NUMBER",
        "boolean": "BOOLEAN",
        "object": "OBJECT",
        "array": "ARRAY",
    }
    t = d.get("type", "string")
    schema_kwargs: dict[str, Any] = {"type": type_map.get(t, "STRING")}
    if t == "object":
        props = {}
        for k, v in d.get("properties", {}).items():
            props[k] = _dict_to_schema(v)
        schema_kwargs["properties"] = props
        if d.get("required"):
            schema_kwargs["required"] = d["required"]
    elif t == "array":
        item_schema = d.get("items", {"type": "string"})
        schema_kwargs["items"] = _dict_to_schema(item_schema)
    if "description" in d:
        schema_kwargs["description"] = d["description"]
    return types.Schema(**schema_kwargs)


def _build_tool_object(specs: list[ToolSpec]) -> types.Tool:
    declarations = [
        types.FunctionDeclaration(
            name=spec.name,
            description=spec.description,
            parameters=_dict_to_schema(spec.parameters),
        )
        for spec in specs
    ]
    return types.Tool(function_declarations=declarations)


def _extract_text(content: types.Content | None) -> str:
    if content is None or not content.parts:
        return ""
    return "".join(p.text for p in content.parts if getattr(p, "text", None))


async def run_agent_loop(
    *,
    system_prompt: str,
    user_message: str,
    tools: list[ToolSpec],
    history: list[dict] | None = None,
    extra_context: dict | None = None,
) -> LLMResponse:
    """Gemini ile tool calling dongusu calistirir.

    history: onceki kullanici/model mesajlari, [{role, parts}] formati
    extra_context: tool handler'lara gecilen ekstra (orn ctx)
    """
    client = _get_client()
    tool_object = _build_tool_object(tools) if tools else None

    contents: list[types.Content] = []
    if history:
        for h in history:
            role = h.get("role", "user")
            text = h.get("content") or h.get("text") or ""
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[tool_object] if tool_object else None,
    )

    tool_calls_made: list[dict] = []

    for _ in range(MAX_ITERATIONS):
        response = await _generate_with_retry(
            client,
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        function_calls = response.function_calls or []
        if not function_calls:
            return LLMResponse(text=(response.text or "").strip(), tool_calls_made=tool_calls_made)

        # Modelin tool cagri Content'ini history'ye ekle
        model_content = response.candidates[0].content if response.candidates else None
        if model_content is None:
            return LLMResponse(text="", tool_calls_made=tool_calls_made)
        contents.append(model_content)

        # Her function call'i sirayla yurut, sonuc Part'larini topla
        response_parts: list[types.Part] = []
        for fc in function_calls:
            tool_name = fc.name
            args = dict(fc.args) if fc.args else {}
            spec = next((t for t in tools if t.name == tool_name), None)
            if spec is None:
                result: dict = {"error": f"Bilinmeyen tool: {tool_name}"}
            else:
                try:
                    kwargs = dict(args)
                    if extra_context:
                        kwargs.update(extra_context)
                    result = await spec.handler(**kwargs)
                except Exception as e:
                    logger.exception("Tool error in %s", tool_name)
                    result = {"error": f"Tool calistirma hatasi: {e}"}
            tool_calls_made.append({"tool": tool_name, "args": args, "result": result})
            response_parts.append(
                types.Part.from_function_response(name=tool_name, response={"result": result})
            )

        contents.append(types.Content(role="tool", parts=response_parts))

    return LLMResponse(
        text="Uzgunum, isteginizi tamamlayamadim. Lutfen daha kisa ifade eder misiniz?",
        tool_calls_made=tool_calls_made,
    )
