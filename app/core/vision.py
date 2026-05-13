"""Gemini Vision ile gorsel urun tanima.

Telegram'dan gelen fotograf:
1. Telegram API'den dosyayi indir
2. Gemini Vision'a gonder
3. Urunu tanimla, DB'deki urunlerle eslestime yap
4. Musteri agent'a ilet
"""

import logging

import httpx
from google.genai import types

from app.core import llm as llm_core
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_telegram_file_url(file_id: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id},
        )
        r.raise_for_status()
        data = r.json()
        file_path = data["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"


async def _download_photo(file_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(file_url)
        r.raise_for_status()
        return r.content


async def identify_product_from_photo(
    file_id: str,
    available_products: list[str],
) -> dict:
    """Fotograftaki urunu tanimla, mevcut urun listesiyle eslestime yap.
    
    Returns:
        {
            "identified": True/False,
            "product_name": "Bal",      # DB'deki urun adi
            "confidence": "high/medium/low",
            "description": "Fotografta bal gorundugu anlasildi",
            "suggested_message": "5 kilo bal istiyorum"  # agent'a gidecek mesaj
        }
    """
    file_url = await _get_telegram_file_url(file_id)
    photo_bytes = await _download_photo(file_url)

    logger.info("Identifying product from photo, size=%d bytes", len(photo_bytes))

    products_str = ", ".join(available_products)

    prompt = f"""Bu fotoğrafı analiz et ve aşağıdaki ürün listesiyle eşleştir.

Mevcut ürünler: {products_str}

Görevin:
1. Fotoğraftaki ürünü veya içeriği tanımla
2. Mevcut ürün listesinden en uygun eşleşmeyi bul
3. Emin değilsen "identified: false" döndür

Sadece JSON formatında yanıt ver, başka hiçbir şey yazma:
{{
  "identified": true/false,
  "product_name": "eşleşen ürün adı veya null",
  "confidence": "high/medium/low",
  "description": "fotoğrafta ne gördüğünün kısa açıklaması",
  "suggested_message": "bu ürünü sipariş etmek istiyorum (miktar belirtme)"
}}"""

    response = await llm_core.generate_content_with_fallback(
        model=settings.GEMINI_MODEL,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            mime_type="image/jpeg",
                            data=photo_bytes,
                        )
                    ),
                    types.Part.from_text(text=prompt),
                ],
            )
        ],
        log_context="Gemini Vision",
    )

    import json
    import re

    text = (response.text or "").strip()
    # JSON bloğunu çıkar
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        logger.warning("No JSON in vision response: %s", text[:200])
        return {"identified": False, "description": text}

    try:
        result = json.loads(match.group())
        logger.info("Product identified: %s (confidence: %s)", 
                   result.get("product_name"), result.get("confidence"))
        return result
    except json.JSONDecodeError:
        logger.warning("Failed to parse vision JSON: %s", text[:200])
        return {"identified": False, "description": text}
