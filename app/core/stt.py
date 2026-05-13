"""STT altyapisi. Default kapali. Aktivasyon icin .env'de STT_ENABLED=true."""

import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class STTDisabledError(Exception):
    """Sesli mesaj transkripsiyon servisi kapali."""


class STTFailedError(Exception):
    """Transkripsiyon basarisiz oldu (network, API, vb.)."""


class Transcriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_url: str, lang: str = "tr") -> str: ...


class DisabledTranscriber(Transcriber):
    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        raise STTDisabledError("STT su an kapali")


class WhisperTranscriber(Transcriber):
    """OpenAI Whisper API ile transkripsiyon. OPENAI_API_KEY .env'de olmali."""

    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if not api_key:
            raise STTFailedError("OPENAI_API_KEY tanimli degil")
        async with httpx.AsyncClient(timeout=60) as client:
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()
            files = {"file": ("voice.ogg", audio_resp.content, "audio/ogg")}
            data = {"model": "whisper-1", "language": lang}
            r = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
            )
            if r.status_code != 200:
                raise STTFailedError(f"Whisper API {r.status_code}: {r.text}")
            return r.json().get("text", "").strip()


class GeminiAudioTranscriber(Transcriber):
    """Gemini multimodal audio input ile transkripsiyon."""

    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        from google import genai
        from google.genai import types

        if not settings.GEMINI_API_KEY:
            raise STTFailedError("GEMINI_API_KEY tanimli degil")

        async with httpx.AsyncClient(timeout=60) as http:
            audio_resp = await http.get(audio_url)
            audio_resp.raise_for_status()
            audio_bytes = audio_resp.content

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        instruction = (
            f"Transcribe the following voice message in {lang}. "
            "Return ONLY the transcribed text, no preamble, no commentary, "
            "no quotes. If the audio is unclear, return your best guess."
        )
        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    instruction,
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                ],
            )
        except Exception as e:
            raise STTFailedError(f"Gemini audio failed: {e}") from e
        text = (response.text or "").strip()
        if not text:
            raise STTFailedError("Bos transkript")
        return text


def get_transcriber() -> Transcriber:
    if not settings.STT_ENABLED:
        return DisabledTranscriber()
    if settings.STT_PROVIDER == "whisper":
        return WhisperTranscriber()
    if settings.STT_PROVIDER == "gemini":
        return GeminiAudioTranscriber()
    return DisabledTranscriber()
