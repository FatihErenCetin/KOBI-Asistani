"""Hazır prompt şablonları — kullanıcı 1 tık ile hızlı post taslağı oluşturur."""

TEMPLATES = [
    {
        "id": "indirim",
        "title": "İndirim Kampanyası",
        "icon": "🏷️",
        "prompt_seed": (
            "{product_name} ürününde özel %{discount} indirim duyurusu. "
            "Aciliyet hissi yarat ('son 3 gün' gibi), Türkçe samimi dil kullan."
        ),
        "default_platforms": ["instagram", "tiktok", "facebook"],
        "needs_product": True,
    },
    {
        "id": "yeni_urun",
        "title": "Yeni Ürün Tanıtımı",
        "icon": "✨",
        "prompt_seed": (
            "{product_name} ürününü tanıt. Hikayesini anlat, faydalarını vurgula. "
            "Hangi mevsime/duruma uygun olduğunu söyle."
        ),
        "default_platforms": ["instagram", "youtube"],
        "needs_product": True,
    },
    {
        "id": "skt_yaklasan",
        "title": "SKT Yaklaşan — Hızlı Tüketim",
        "icon": "⏳",
        "prompt_seed": (
            "{product_name} ürünü kısa süre içinde son kullanma tarihine yaklaşıyor "
            "({days_left} gün kaldı). %{discount} indirimle hızlı satış. "
            "Pozitif dil — 'taze, hemen al' vurgusu."
        ),
        "default_platforms": ["instagram", "facebook"],
        "needs_product": True,
    },
    {
        "id": "sezon",
        "title": "Sezon Başlangıcı",
        "icon": "🌸",
        "prompt_seed": (
            "{season_name} sezonu başladı. {product_category} kategorisinde "
            "öne çıkanlarımız. Türkçe samimi, müşteriyle bağlantı kuran dil."
        ),
        "default_platforms": ["instagram", "tiktok", "facebook"],
        "needs_product": False,
    },
    {
        "id": "musteri_yorumu",
        "title": "Müşteri Yorumu Paylaşımı",
        "icon": "💬",
        "prompt_seed": (
            "Müşteri yorumlarımızı yansıtan bir post. Güven inşa et, "
            "ürün kalitesini yorumlardan örnekle göster."
        ),
        "default_platforms": ["instagram", "facebook"],
        "needs_product": False,
    },
    {
        "id": "behind_scenes",
        "title": "Perde Arkası",
        "icon": "🎬",
        "prompt_seed": (
            "İşletmenin perde arkasını göster: hazırlık süreci, ekip, mekan. "
            "Samimi, gerçek hayat hissi veren."
        ),
        "default_platforms": ["instagram", "tiktok", "youtube"],
        "needs_product": False,
    },
    {
        "id": "tarif_ipucu",
        "title": "Tarif / İpucu",
        "icon": "🍳",
        "prompt_seed": (
            "{product_name} ile yapılabilecek bir tarif veya kullanım ipucu. "
            "Adım adım, kısa, ilham verici."
        ),
        "default_platforms": ["instagram", "tiktok", "youtube"],
        "needs_product": True,
    },
    {
        "id": "stok_tukenmek_uzere",
        "title": "Stok Bitmek Üzere",
        "icon": "⚡",
        "prompt_seed": (
            "{product_name} stoğumuzun son kısmı kaldı ({stock} {unit}). "
            "FOMO yarat: 'kaçırma, son fırsat'. Kibarca."
        ),
        "default_platforms": ["instagram", "tiktok"],
        "needs_product": True,
    },
]


def get_template(template_id: str) -> dict | None:
    return next((t for t in TEMPLATES if t["id"] == template_id), None)
