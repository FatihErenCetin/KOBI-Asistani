"""Gemini Vision urun tanima testleri (LLM mock'lu)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core import vision


@pytest.mark.asyncio
async def test_identify_returns_unidentified_when_no_api_key():
    """Settings'te key yoksa identified=False döner, fotoğraf indirilmez bile."""
    with patch.object(vision.settings, "GEMINI_API_KEY", ""), patch.object(
        vision.settings, "GEMINI_API_KEYS", ""
    ):
        result = await vision.identify_product_from_photo("fake_file_id", ["Bal"])
    assert result["identified"] is False
    assert result["product_name"] is None


@pytest.mark.asyncio
async def test_identify_parses_json_response():
    """Geçerli JSON gelirse parse edilip listeden eşleşme yapılır."""
    fake_response = MagicMock()
    fake_response.text = '{"identified": true, "product_name": "Bal", "confidence": "high", "description": "Cam kavanozda bal", "suggested_message": "2 kilo bal istiyorum"}'

    with patch.object(
        vision, "_get_telegram_file_url", new=AsyncMock(return_value="http://x")
    ), patch.object(
        vision, "_download_photo", new=AsyncMock(return_value=b"fake")
    ), patch.object(
        vision.llm_core,
        "generate_content_with_fallback",
        new=AsyncMock(return_value=fake_response),
    ):
        result = await vision.identify_product_from_photo("fid", ["Bal", "Zeytinyağı"])

    assert result["identified"] is True
    assert result["product_name"] == "Bal"  # listede tam eşleşme bulundu
    assert result["confidence"] == "high"
    assert "2 kilo" in result["suggested_message"]


@pytest.mark.asyncio
async def test_identify_strips_markdown_fence():
    """LLM ```json bloğu ile dönerse temizleyebilmeli."""
    fake_response = MagicMock()
    fake_response.text = '```json\n{"identified": true, "product_name": "Domates", "confidence": "medium", "description": "salkim domates", "suggested_message": "domates"}\n```'

    with patch.object(
        vision, "_get_telegram_file_url", new=AsyncMock(return_value="http://x")
    ), patch.object(
        vision, "_download_photo", new=AsyncMock(return_value=b"fake")
    ), patch.object(
        vision.llm_core,
        "generate_content_with_fallback",
        new=AsyncMock(return_value=fake_response),
    ):
        result = await vision.identify_product_from_photo("fid", ["Domates"])

    assert result["identified"] is True
    assert result["product_name"] == "Domates"


@pytest.mark.asyncio
async def test_identify_rejects_when_product_not_in_list():
    """LLM listede olmayan ürün önerirse identified=False'a düşürülmeli."""
    fake_response = MagicMock()
    fake_response.text = '{"identified": true, "product_name": "Çikolata", "confidence": "high", "description": "tablet", "suggested_message": "çikolata istiyorum"}'

    with patch.object(
        vision, "_get_telegram_file_url", new=AsyncMock(return_value="http://x")
    ), patch.object(
        vision, "_download_photo", new=AsyncMock(return_value=b"fake")
    ), patch.object(
        vision.llm_core,
        "generate_content_with_fallback",
        new=AsyncMock(return_value=fake_response),
    ):
        result = await vision.identify_product_from_photo("fid", ["Bal", "Zeytinyağı"])

    assert result["identified"] is False
    assert result["product_name"] is None


@pytest.mark.asyncio
async def test_identify_handles_invalid_json():
    """LLM bozuk metin dönerse graceful başarısızlık."""
    fake_response = MagicMock()
    fake_response.text = "Anlamadım bu fotoğrafı."

    with patch.object(
        vision, "_get_telegram_file_url", new=AsyncMock(return_value="http://x")
    ), patch.object(
        vision, "_download_photo", new=AsyncMock(return_value=b"fake")
    ), patch.object(
        vision.llm_core,
        "generate_content_with_fallback",
        new=AsyncMock(return_value=fake_response),
    ):
        result = await vision.identify_product_from_photo("fid", ["Bal"])

    assert result["identified"] is False
