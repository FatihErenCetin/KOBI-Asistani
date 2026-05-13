"""Sosyal medya post taslagi ureten AI agent.

Kullanici niyeti + (opsiyonel) urun bilgisi → Gemini structured JSON cevabi:
{title, content, hashtags, image_prompt, video_prompt, suggested_platforms}

LLM hata verirse deterministik fallback (sablon + product info).
"""

import json
import logging
import re

from app.core.config import settings
from app.core import llm as llm_core

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Sen bir KOBİ sosyal medya editörüsün. Verilen niyete göre
çoklu platforma uygun (Instagram, TikTok, Facebook, YouTube Shorts) bir post
taslağı üret. Türkçe konuş, Türkçe karakterleri tam kullan
(ş, ç, ğ, ü, ö, ı, İ). Cana yakın, satış odaklı ama samimi bir ton.

ÇIKTI SADECE JSON, başka HİÇBİR ŞEY:
{
  "title": "<dahili etiket, 60 karakter altı>",
  "content": "<Türkçe post metni, 200-400 karakter, satırlar emojili olabilir>",
  "hashtags": ["#hashtag1", "#hashtag2", ...],
  "image_prompt": "<görsel üretim için İngilizce kısa prompt, fotoğraf stilinde>",
  "video_prompt": "<6-10 saniyelik kısa video prompt, İngilizce>",
  "suggested_platforms": ["instagram", "tiktok", ...]
}

content'te ürün adı net geçsin. Aciliyet hissi varsa (indirim, son fırsat)
kibarca vurgula. Hashtag'ler Türkçe veya İngilizce olabilir, 5-10 adet.
"""


def _strip_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # ```json ... ```
        inner = t.split("```", 2)
        if len(inner) >= 2:
            t = inner[1]
            t = re.sub(r"^json\s*", "", t).strip()
    return t


def _fallback_draft(
    prompt: str,
    *,
    product_name: str | None = None,
    product_description: str | None = None,
    discount_pct: float | None = None,
    target_platforms: list[str] | None = None,
    # Backwards compat alias
    platforms: list[str] | None = None,
) -> dict:
    """LLM olmadiginda deterministik sablon. Indirim + urun bilgisini kullanir."""
    plats = target_platforms or platforms
    name = product_name or "ürünümüz"
    discount_line = ""
    if discount_pct:
        discount_line = f"🏷️ Bu hafta %{int(discount_pct)} indirim! "
    desc_line = f"{product_description}\n\n" if product_description else ""
    content = (
        f"✨ {name} için özel bir duyurumuz var!\n\n"
        f"{discount_line}{prompt[:150]}\n\n{desc_line}"
        "Detaylar mağazamızda, mesaj atıp bilgi alabilirsiniz."
    ).strip()
    return {
        "title": f"{name} - Sosyal Medya Postu",
        "content": content,
        "hashtags": [
            "#kobi",
            "#yerelmarka",
            "#dogal",
            f"#{(product_name or 'urun').lower().replace(' ', '')}",
            *(["#indirim", "#kampanya"] if discount_pct else []),
        ],
        "image_prompt": f"Beautiful product photo of {name}, natural light, lifestyle, instagram aesthetic",
        "video_prompt": f"Short product showcase of {name}, dynamic camera, warm tones, 8 seconds",
        "suggested_platforms": plats or ["instagram", "facebook"],
    }


async def draft_post(
    prompt: str,
    *,
    product_name: str | None = None,
    product_description: str | None = None,
    discount_pct: float | None = None,
    target_platforms: list[str] | None = None,
) -> dict:
    """Kullanici niyetinden bir post taslagi uret."""
    if not settings.GEMINI_API_KEY and not settings.gemini_api_keys_list:
        return _fallback_draft(
            prompt,
            product_name=product_name,
            product_description=product_description,
            discount_pct=discount_pct,
            target_platforms=target_platforms,
        )

    context_parts = [f"Kullanıcı niyeti: {prompt}"]
    if product_name:
        context_parts.append(f"Ürün: {product_name}")
    if product_description:
        context_parts.append(f"Ürün özelliği: {product_description}")
    if discount_pct:
        context_parts.append(f"İndirim: %{discount_pct}")
    if target_platforms:
        context_parts.append(f"Hedef platformlar: {', '.join(target_platforms)}")
    user_input = "\n".join(context_parts)

    try:
        from google.genai import types

        response = await llm_core.generate_content_with_fallback(
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_input)],
                )
            ],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        raw = (response.text or "").strip()
        raw = _strip_fence(raw)
        data = json.loads(raw)

        # Validation
        return {
            "title": str(data.get("title", ""))[:200],
            "content": str(data.get("content", ""))[:2800],
            "hashtags": [
                str(h).strip()
                for h in (data.get("hashtags") or [])
                if str(h).strip()
            ][:15],
            "image_prompt": str(data.get("image_prompt", ""))[:500],
            "video_prompt": str(data.get("video_prompt", ""))[:500],
            "suggested_platforms": [
                str(p).strip().lower()
                for p in (data.get("suggested_platforms") or [])
                if str(p).strip()
            ]
            or (target_platforms or ["instagram"]),
        }
    except Exception as e:
        logger.warning("Social agent LLM failed, using fallback: %s", e)
        return _fallback_draft(
            prompt,
            product_name=product_name,
            product_description=product_description,
            discount_pct=discount_pct,
            target_platforms=target_platforms,
        )
