import pytest

from app.core import identity, stt


def test_normalize_phone():
    assert identity.normalize_phone("+90 555 123 45 67") == "+905551234567"
    assert identity.normalize_phone("05551234567") == "+05551234567"


def test_stt_disabled_by_default():
    t = stt.get_transcriber()
    assert isinstance(t, stt.DisabledTranscriber)


@pytest.mark.asyncio
async def test_disabled_transcriber_raises():
    t = stt.DisabledTranscriber()
    with pytest.raises(stt.STTDisabledError):
        await t.transcribe("http://fake")


@pytest.mark.asyncio
async def test_link_telegram_creates_customer(db):
    c = await identity.link_telegram_to_phone(db, 12345, "+905551112233")
    assert c.telegram_user_id == 12345
    assert c.phone == "+905551112233"
