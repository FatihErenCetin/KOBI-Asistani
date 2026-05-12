import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, token: str | None = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base = f"https://api.telegram.org/bot{self.token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_markup: dict | None = None,
        parse_mode: str = "HTML",
    ) -> dict:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self.base}/sendMessage", json=payload)
            r.raise_for_status()
            return r.json()

    async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{self.base}/sendChatAction",
                json={"chat_id": chat_id, "action": action},
            )

    async def answer_callback_query(
        self, callback_id: str, text: str | None = None
    ) -> None:
        payload: dict[str, Any] = {"callback_query_id": callback_id}
        if text:
            payload["text"] = text
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{self.base}/answerCallbackQuery", json=payload)

    async def get_file_url(self, file_id: str) -> str:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base}/getFile", params={"file_id": file_id})
            r.raise_for_status()
            file_path = r.json()["result"]["file_path"]
            return f"https://api.telegram.org/file/bot{self.token}/{file_path}"

    async def set_webhook(self, url: str, secret_token: str | None = None) -> dict:
        payload: dict[str, Any] = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{self.base}/setWebhook", json=payload)
            r.raise_for_status()
            return r.json()


telegram_client = TelegramClient()
