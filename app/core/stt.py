"""Telegram sesli mesaj transkripsiyonu.

Varsayılan akış Gemini ile çalışır:
1. Telegram file_id ile ses dosyası indirilir
2. Gemini audio understanding ile Türkçe metne çevrilir
3. Çıkan metin normal müşteri/panel agent akışına gönderilir

İstenirse STT_PROVIDER=groq verilerek Groq Whisper yedek olarak kullanılabilir.
"""

import logging

import httpx
from google.genai import types

from app.core import llm as llm_core
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_telegram_file_url(file_id: str) -> str:
    """Telegram file_id'den indirme URL'i al."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id},
        )
        r.raise_for_status()
        data = r.json()
        file_path = data["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"


async def _download_voice(file_url: str) -> bytes:
    """Telegram'dan ses dosyasini indir."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(file_url)
        r.raise_for_status()
        return r.content


def _guess_audio_mime(file_url: str) -> str:
    lowered = file_url.lower()
    if lowered.endswith(".mp3"):
        return "audio/mpeg"
    if lowered.endswith(".wav"):
        return "audio/wav"
    if lowered.endswith(".m4a"):
        return "audio/mp4"
    # Telegram voice mesajları çoğunlukla ogg/opus gelir.
    return "audio/ogg"


async def _transcribe_with_gemini(audio_bytes: bytes, mime_type: str) -> str:
    prompt = (
        "Bu sesli mesajı Türkçe olarak yazıya çevir. "
        "Sadece konuşulan metni döndür. Açıklama, yorum, başlık veya tırnak işareti ekleme."
    )
    response = await llm_core.generate_content_with_fallback(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=audio_bytes,
                        )
                    ),
                    types.Part.from_text(text=prompt),
                ],
            )
        ],
        log_context="Gemini STT",
    )
    return (response.text or "").strip()


async def _transcribe_with_groq(audio_bytes: bytes) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    # Groq paketinin kurulu olmadığı senaryoda backend import sırasında düşmesin diye lazy import.
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    transcription = await client.audio.transcriptions.create(
        file=("voice.ogg", audio_bytes, "audio/ogg"),
        model="whisper-large-v3-turbo",
        language="tr",
        response_format="text",
    )
    return str(transcription).strip()


async def transcribe_voice(file_id: str) -> str:
    """Telegram voice mesajini metne çevir."""
    file_url = await _get_telegram_file_url(file_id)
    audio_bytes = await _download_voice(file_url)
    mime_type = _guess_audio_mime(file_url)

    logger.info("Transcribing voice message, provider=%s, size=%d bytes", settings.STT_PROVIDER, len(audio_bytes))

    provider = (settings.STT_PROVIDER or "gemini").lower().strip()

    if provider in {"groq", "whisper"}:
        try:
            transcript = await _transcribe_with_groq(audio_bytes)
            logger.info("Groq transcription result: %s", transcript[:100])
            return transcript
        except Exception:
            logger.exception("Groq transcription failed, trying Gemini fallback")

    transcript = await _transcribe_with_gemini(audio_bytes, mime_type)
    logger.info("Gemini transcription result: %s", transcript[:100])
    return transcript
