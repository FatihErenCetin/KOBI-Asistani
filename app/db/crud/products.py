import re
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product


_TR_CHARS = str.maketrans(
    {
        "ç": "c",
        "Ç": "c",
        "ğ": "g",
        "Ğ": "g",
        "ı": "i",
        "I": "i",
        "İ": "i",
        "ö": "o",
        "Ö": "o",
        "ş": "s",
        "Ş": "s",
        "ü": "u",
        "Ü": "u",
    }
)


def normalize_text(value: str | None) -> str:
    """Türkçe karakter, noktalama ve fazla boşluk toleranslı arama metni üretir.

    Örnekler:
    - "Çay" -> "cay"
    - "cay" -> "cay"
    - "zeytin yağı" -> "zeytin yagi"
    """
    if not value:
        return ""
    value = value.translate(_TR_CHARS)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _product_terms(product: Product) -> list[str]:
    terms = [product.name]
    if product.aliases:
        terms.extend([part.strip() for part in product.aliases.split(",") if part.strip()])
    return terms


def _score_product(product: Product, query: str) -> int:
    query_norm = normalize_text(query)
    if not query_norm:
        return 0

    terms = _product_terms(product)
    normalized_terms = [normalize_text(term) for term in terms if normalize_text(term)]
    haystack = " ".join(normalized_terms)

    if query_norm in normalized_terms:
        return 100
    if any(query_norm == term or query_norm in term or term in query_norm for term in normalized_terms):
        return 90

    query_tokens = set(query_norm.split())
    haystack_tokens = set(haystack.split())
    if query_tokens and query_tokens.issubset(haystack_tokens):
        return 80

    overlap = len(query_tokens & haystack_tokens)
    if overlap:
        return 50 + overlap

    best_similarity = max(
        (SequenceMatcher(None, query_norm, term).ratio() for term in normalized_terms),
        default=0,
    )
    if best_similarity >= 0.82:
        return int(best_similarity * 50)
    return 0


async def get_by_id(db: AsyncSession, product_id: int) -> Product | None:
    return await db.get(Product, product_id)


async def search_by_name(db: AsyncSession, query: str, limit: int = 10) -> list[Product]:
    """Ürün adını Türkçe karakter ve alias toleransıyla arar.

    DB'de ürün adı "Çay" olsa da kullanıcı/Gemini "cay" yazarsa ürün bulunur.
    Aynı şekilde "fındık/findik", "zeytinyağı/zeytinyagi" gibi eşleşmeler çalışır.
    """
    query = (query or "").strip()
    if not query:
        return []

    # Önce ucuz SQL filtresi: direkt ad veya alias içinde geçen kayıtları öne al.
    pattern = f"%{query}%"
    normalized_query = normalize_text(query)
    normalized_pattern = f"%{normalized_query}%"
    res = await db.execute(
        select(Product).where(
            or_(
                Product.name.ilike(pattern),
                Product.aliases.ilike(pattern),
                Product.name.ilike(normalized_pattern),
                Product.aliases.ilike(normalized_pattern),
            )
        )
    )
    direct_matches = list(res.scalars())

    # SQL eşleşmezse tüm ürünleri normalize ederek tara. Katalog küçük olduğu için demo için güvenli.
    if not direct_matches:
        res = await db.execute(select(Product))
        direct_matches = list(res.scalars())

    scored = [(p, _score_product(p, query)) for p in direct_matches]
    scored = [(p, score) for p, score in scored if score > 0]
    scored.sort(key=lambda item: (-item[1], item[0].name))
    return [p for p, _ in scored[:limit]]


async def list_all(
    db: AsyncSession, low_stock_only: bool = False, search: str | None = None
) -> list[Product]:
    stmt = select(Product)
    if low_stock_only:
        stmt = stmt.where(Product.stock <= Product.low_stock_threshold)
    if search:
        # Listeleme ekranında da Türkçe karakter toleransı olsun.
        products = await search_by_name(db, search, limit=100)
        if low_stock_only:
            products = [p for p in products if p.stock <= p.low_stock_threshold]
        return sorted(products, key=lambda p: p.name)
    res = await db.execute(stmt.order_by(Product.name))
    return list(res.scalars())


async def adjust_stock(db: AsyncSession, product: Product, delta: float) -> Product:
    product.stock = max(0.0, product.stock + delta)
    await db.flush()
    return product


async def set_stock(db: AsyncSession, product: Product, stock: float) -> Product:
    product.stock = max(0.0, stock)
    await db.flush()
    return product
