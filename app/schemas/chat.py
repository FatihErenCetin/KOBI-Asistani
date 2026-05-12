from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None


class ChatResponse(BaseModel):
    text: str
    data: dict[str, Any] | None = None
