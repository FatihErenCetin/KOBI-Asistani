"""STT altyapisi. Default kapali. Aktivasyon icin .env'de STT_ENABLED=true."""

from abc import ABC, abstractmethod

from app.core.config import settings


class STTDisabledError(Exception):
    """Sesli mesaj transkripsiyon servisi kapali."""


class Transcriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_url: str, lang: str = "tr") -> str: ...


class DisabledTranscriber(Transcriber):
    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        raise STTDisabledError("STT su an kapali")


class WhisperTranscriber(Transcriber):
    """Aktivasyon sirasinda openai/whisper SDK ya da local whisper.cpp baglanir."""

    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        raise NotImplementedError("Aktivasyonda implement edilecek")


class GeminiAudioTranscriber(Transcriber):
    """Gemini multimodal audio input ile."""

    async def transcribe(self, audio_url: str, lang: str = "tr") -> str:
        raise NotImplementedError("Aktivasyonda implement edilecek")


def get_transcriber() -> Transcriber:
    if not settings.STT_ENABLED:
        return DisabledTranscriber()
    if settings.STT_PROVIDER == "whisper":
        return WhisperTranscriber()
    if settings.STT_PROVIDER == "gemini":
        return GeminiAudioTranscriber()
    return DisabledTranscriber()
