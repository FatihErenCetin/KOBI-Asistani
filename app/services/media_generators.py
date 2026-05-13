"""Görsel ve video üretim servisleri.

Provider interface deseni: gerçek API key (.env'de) varsa o provider, yoksa
placeholder. Bu sayede ileride OPENAI_API_KEY, REPLICATE_API_TOKEN gibi key'ler
eklendiğinde sistem otomatik gerçek API'yi kullanır.

Provider sözleşmesi:
- async generate(prompt: str) -> dict  # {url, provider, error?}
"""

import hashlib
import logging
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerator(Protocol):
    async def generate(self, prompt: str, size: str = "1024x1024") -> dict: ...


class VideoGenerator(Protocol):
    async def generate(self, prompt: str, duration_seconds: int = 6) -> dict: ...


# ---------- Placeholder (Mock) ----------


def _hash_prompt(prompt: str) -> str:
    return hashlib.md5(prompt.encode("utf-8")).hexdigest()[:10]


class PlaceholderImageGenerator:
    """picsum.photos üzerinden deterministik placeholder görsel.

    Aynı prompt → aynı görsel (seed=hash). KOBİ demo için yeterli; gerçek
    API entegre edildiğinde bu provider yedek/test rolünde kalır.
    """

    name = "placeholder"

    async def generate(self, prompt: str, size: str = "1024x1024") -> dict:
        seed = _hash_prompt(prompt)
        # picsum.photos boyut formatı: /WIDTH/HEIGHT
        try:
            w, h = (int(x) for x in size.split("x"))
        except ValueError:
            w, h = 1024, 1024
        url = f"https://picsum.photos/seed/{seed}/{w}/{h}"
        logger.info("Placeholder image generated: %s", url)
        return {"url": url, "provider": self.name, "prompt": prompt}


class PlaceholderVideoGenerator:
    """Video API'si bağlı olmadığında 'hazırlanıyor' durumu döner.

    Gerçek implementasyon Veo/Sora/Replicate ile yapılır; o güne kadar
    UI'da 'video API yakında' mesajı görünür.
    """

    name = "placeholder"

    async def generate(self, prompt: str, duration_seconds: int = 6) -> dict:
        return {
            "url": None,
            "provider": self.name,
            "prompt": prompt,
            "error": (
                "Video oluşturma API anahtarı tanımlı değil. "
                ".env'ye OPENAI_API_KEY veya REPLICATE_API_TOKEN ekleyin."
            ),
        }


# ---------- OpenAI DALL-E (gerçek, API key gelince aktive olur) ----------


class OpenAIImageGenerator:
    name = "openai"

    async def generate(self, prompt: str, size: str = "1024x1024") -> dict:
        api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        if not api_key:
            return {
                "url": None,
                "provider": self.name,
                "prompt": prompt,
                "error": "OPENAI_API_KEY tanımlı değil",
            }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": size,
                    },
                )
                if r.status_code != 200:
                    return {
                        "url": None,
                        "provider": self.name,
                        "prompt": prompt,
                        "error": f"OpenAI {r.status_code}: {r.text[:200]}",
                    }
                url = r.json()["data"][0]["url"]
                return {"url": url, "provider": self.name, "prompt": prompt}
        except Exception as e:
            return {
                "url": None,
                "provider": self.name,
                "prompt": prompt,
                "error": str(e),
            }


# ---------- Factory ----------


def get_image_generator() -> ImageGenerator:
    """Settings'e göre uygun image provider'ı döner. Default: placeholder."""
    provider = (getattr(settings, "IMAGE_PROVIDER", "") or "placeholder").lower()
    if provider == "openai":
        return OpenAIImageGenerator()
    return PlaceholderImageGenerator()


def get_video_generator() -> VideoGenerator:
    """Video provider — şu an sadece placeholder (API entegrasyonu hazır değil)."""
    # İleride: provider == "replicate" / "veo" durumunda ilgili implementation
    return PlaceholderVideoGenerator()
