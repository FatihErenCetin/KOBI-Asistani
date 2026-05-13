"""Gemini Vision ile fotograftan urun tanima.

Telegram'dan gelen fotograf:
1. Telegram API'den dosyayi indir
2. Gemini Vision'a urun listesiyle birlikte gonder (structured prompt)
3. JSON cevap parse et: identified, product_name, confidence, suggested_message
4. Customer agent'a 'suggested_message' iletilebilir (5 kilo bal istiyorum gibi)

LLM hata verirse veya yetersiz guvenle tanirsa identified=False doner;
caller sesli olmadan kullaniciya 'fotografi anlamadim, yazili gonderin' diyebilir.
"""

import json
import logging

import httpx
from google.genai import types

from app.core import llm as llm_core
from app.core.config import settings

logger = logging.getLogger(__name__)


VISION_PROMPT = """Sen bir KOBİ asistanısın. Müşteri sana bir ürün fotoğrafı gönderdi.
Aşağıdaki ürün listesinden fotoğraftaki ürünü tespit et.
Türkçe karakterleri tam kullan (ş, ç, ğ, ü, ö, ı, İ).

ÇIKTI SADECE şu JSON formatında, başka HİÇBİR ŞEY yazma:
{
  "identified": true/false,
  "product_name": "<liste'deki birebir ürün adı veya null>",
  "confidence": "high|medium|low",
  "description": "<fotoğrafta ne gördüğüne dair 1 cümle>",
  "suggested_message": "<müşteri yerine yazılacak metin, örn: '2 kilo bal istiyorum'>"
}

identified=true sadece confidence yüksek/orta ve listede eşleşme varsa.
suggested_message müşterinin kastettiği niyeti içerir (ürün adı + tahmini miktar).

Mevcut ürünler: {products}"""


async def _get_telegram_file_url(file_id: str) -> str:
    """Telegram getFile API ile dosya URL'sini al."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile",
            params={"file_id": file_id},
        )
        r.raise_for_status()
        file_path = r.json()["result"]["file_path"]
        return f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"


async def _download_photo(file_url: str) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(file_url)
        r.raise_for_status()
        return r.content


async def identify_product_from_photo(
    file_id: str, available_products: list[str]
) -> dict:
    """Fotograftaki urunu tanimla.

    Returns:
        {
            "identified": bool,
            "product_name": str | None,
            "confidence": "high|medium|low" | None,
            "description": str,
            "suggested_message": str | None
        }
    """
    if not settings.GEMINI_API_KEY and not settings.gemini_api_keys_list:
        return {
            "identified": False,
            "product_name": None,
            "confidence": None,
            "description": "Gemini API key tanimli degil",
            "suggested_message": None,
        }

    try:
        file_url = await _get_telegram_file_url(file_id)
        photo_bytes = await _download_photo(file_url)
    except Exception as e:
        logger.warning("Photo download failed: %s", e)
        return {
            "identified": False,
            "product_name": None,
            "confidence": None,
            "description": f"Fotograf indirilemedi: {e}",
            "suggested_message": None,
        }

    products_str = ", ".join(available_products) or "(liste bos)"
    prompt = VISION_PROMPT.replace("{products}", products_str)

    try:
        response = await llm_core.generate_content_with_fallback(
            contents=[
                prompt,
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
            ],
        )
    except Exception as e:
        logger.warning("Vision LLM call failed: %s", e)
        return {
            "identified": False,
            "product_name": None,
            "confidence": None,
            "description": f"Vision hatasi: {e}",
            "suggested_message": None,
        }

    text = (response.text or "").strip()
    # Markdown code fence temizle
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text[3:] else text
        text = text.lstrip("json").strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Vision response parse failed: %s", text[:200])
        return {
            "identified": False,
            "product_name": None,
            "confidence": None,
            "description": "Cevap formati bozuk",
            "suggested_message": None,
        }

    # Listedeki urun adlariyla case-insensitive eslesme dogrulamasi
    pname = data.get("product_name")
    if pname:
        match = next(
            (p for p in available_products if p.lower() == str(pname).lower()),
            None,
        )
        data["product_name"] = match  # yoksa None
        if match is None:
            data["identified"] = False

    return {
        "identified": bool(data.get("identified", False)),
        "product_name": data.get("product_name"),
        "confidence": data.get("confidence"),
        "description": data.get("description", "")[:300],
        "suggested_message": data.get("suggested_message"),
    }
