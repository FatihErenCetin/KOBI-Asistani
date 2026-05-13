"""Sikayet riski tespiti — regex onfiltre + LLM nuance skoru.

Yaklasim:
1. Regex ile hizli sinyal tara: 'iade', 'sikayet', 'memnun degil', 'kotu', 'bozuk' vs.
   Sinyal yoksa → 0.0 skor, LLM cagrilmaz (quota tasarrufu).
2. Sinyal varsa → Gemini'ye sor: 'Bu mesajda sikayet sinyali var mi? 0-1 skor ver.'
3. Skor 0.7+ → CustomerComplaint olarak kaydet.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Hizli sinyal regex'leri (case-insensitive)
COMPLAINT_PATTERNS = [
    r"\biade\b",
    r"\bgeri\s+ver",
    r"\bsikayet",
    r"\bşikayet",
    r"\bmemnun\s+değil",
    r"\bmemnun\s+degil",
    r"\bkötü",
    r"\bkotu",
    r"\bbozuk",
    r"\bbozulmuş",
    r"\bçürük",
    r"\bcuruk",
    r"\beksik",
    r"\bhatalı",
    r"\bhatali",
    r"\bgeç\s+geldi",
    r"\bgec\s+geldi",
    r"\bçok\s+pahalı",
    r"\bcok\s+pahali",
    r"\bberbat",
    r"\brezalet",
    r"\bskandal",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in COMPLAINT_PATTERNS]


def detect_signals(text: str) -> list[str]:
    """Mesajda eslesen sinyal sozcuklerini doner."""
    found = []
    for pat, raw in zip(_compiled, COMPLAINT_PATTERNS):
        m = pat.search(text)
        if m:
            found.append(m.group(0))
    return found


async def classify_risk(text: str) -> tuple[float, list[str]]:
    """Mesajin sikayet riski skoru + tetikleyen sinyaller.

    Returns: (score 0-1, signals list)
    - Regex sinyal yoksa: (0.0, [])
    - Sinyal varsa LLM'ye sor; LLM hata verirse signals'a gore heuristik skor.
    """
    signals = detect_signals(text)
    if not signals:
        return (0.0, [])

    # LLM nuance — Gemini'ye sor
    try:
        from google import genai

        from app.core.config import settings

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("no api key")
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "Aşağıdaki müşteri mesajında şikayet sinyali var mı? "
            "0 ile 1 arasında bir skor ver (sadece sayı, başka bir şey yazma). "
            "0 = nötr/sorun yok, 0.5 = belirsiz endişe, 0.9+ = açık şikayet/iade talebi.\n\n"
            f"Mesaj: {text}\n\nSkor:"
        )
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt
        )
        raw = (response.text or "0").strip()
        m = re.search(r"\d*\.?\d+", raw)
        score = float(m.group(0)) if m else 0.5
        score = max(0.0, min(1.0, score))
        return (score, signals)
    except Exception as e:
        logger.warning("LLM risk classify failed, using heuristic: %s", e)
        # Heuristik: kac sinyal varsa o kadar yüksek skor (max 0.85)
        return (min(0.85, 0.5 + 0.15 * len(signals)), signals)
