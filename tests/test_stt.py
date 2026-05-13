"""M12: STT — disabled default + provider switching."""

from unittest.mock import patch

import pytest

from app.core import stt
from app.core.stt import (
    DisabledTranscriber,
    GeminiAudioTranscriber,
    STTDisabledError,
    WhisperTranscriber,
    get_transcriber,
)


def test_default_disabled():
    with patch.object(stt.settings, "STT_ENABLED", False):
        t = get_transcriber()
        assert isinstance(t, DisabledTranscriber)


def test_provider_whisper():
    with patch.object(stt.settings, "STT_ENABLED", True), patch.object(
        stt.settings, "STT_PROVIDER", "whisper"
    ):
        t = get_transcriber()
        assert isinstance(t, WhisperTranscriber)


def test_provider_gemini():
    with patch.object(stt.settings, "STT_ENABLED", True), patch.object(
        stt.settings, "STT_PROVIDER", "gemini"
    ):
        t = get_transcriber()
        assert isinstance(t, GeminiAudioTranscriber)


def test_unknown_provider_falls_back_to_disabled():
    with patch.object(stt.settings, "STT_ENABLED", True), patch.object(
        stt.settings, "STT_PROVIDER", "random"
    ):
        t = get_transcriber()
        assert isinstance(t, DisabledTranscriber)


@pytest.mark.asyncio
async def test_disabled_raises():
    t = DisabledTranscriber()
    with pytest.raises(STTDisabledError):
        await t.transcribe("http://x")
