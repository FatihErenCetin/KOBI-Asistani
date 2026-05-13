"""Mevcut demo veritabanındaki ürün adlarını Türkçeleştirir ve alias'ları genişletir.

Kullanım:
    python -m app.db.normalize_product_names

Bu script müşteri, sipariş ve Telegram eşleşmelerini silmez. Sadece products tablosundaki
ad/alias alanlarını günceller. Bu yüzden hackathon demosu sırasında güvenle çalıştırılabilir.
"""

import asyncio

from sqlalchemy import select

from app.db.crud.products import normalize_text
from app.db.models import Product
from app.db.session import SessionLocal


PRODUCT_NAME_UPDATES: dict[str, tuple[str, str]] = {
    "Bal": ("Bal", "çiçek balı,cicek bali,süzme bal,suzme bal,doğal bal,dogal bal"),
    "Zeytinyagi": ("Zeytinyağı", "zeytinyagi,zeytin yağı,zeytin yagi,naturel sızma,naturel sizma"),
    "Domates": ("Domates", "salkım domates,salkim domates,kuru domates"),
    "Biber": ("Biber", "yeşil biber,yesil biber,sivri biber"),
    "Salca": ("Salça", "salca,domates salçası,domates salcasi,biber salçası,biber salcasi"),
    "Recel": ("Reçel", "recel,kayısı reçeli,kayisi receli,vişne reçeli,visne receli"),
    "Peynir": ("Peynir", "beyaz peynir,kaşar,kasar"),
    "Yogurt": ("Yoğurt", "yogurt,süzme yoğurt,suzme yogurt,kaymaklı,kaymakli"),
    "Tereyagi": ("Tereyağı", "tereyagi,köy tereyağı,koy tereyagi,tuzsuz tereyağı,tuzsuz tereyagi"),
    "Yumurta": ("Yumurta", "köy yumurtası,koy yumurtasi,gezen tavuk yumurtası,gezen tavuk yumurtasi"),
    "Un": ("Un", "tam buğday unu,tam bugday unu"),
    "Bulgur": ("Bulgur", "kepekli bulgur,pilavlık bulgur,pilavlik bulgur"),
    "Mercimek": ("Mercimek", "kırmızı mercimek,kirmizi mercimek,yeşil mercimek,yesil mercimek"),
    "Nohut": ("Nohut", "iri nohut"),
    "Fasulye": ("Fasulye", "kuru fasulye,ispir fasulyesi"),
    "Pirinc": ("Pirinç", "pirinc,baldo pirinç,baldo pirinc"),
    "Ceviz": ("Ceviz", "iç ceviz,ic ceviz"),
    "Findik": ("Fındık", "findik,iç fındık,ic findik"),
    "Kuru Uzum": ("Kuru Üzüm", "kuru uzum,üzüm,uzum,sultaniye"),
    "Kuru Incir": ("Kuru İncir", "kuru incir,incir"),
    "Pekmez": ("Pekmez", "üzüm pekmezi,uzum pekmezi,dut pekmezi"),
    "Tarhana": ("Tarhana", "ev tarhanası,ev tarhanasi"),
    "Sirke": ("Sirke", "üzüm sirkesi,uzum sirkesi,elma sirkesi"),
    "Susam Yagi": ("Susam Yağı", "susam yagi,susam yağı,tahin"),
    "Kekik": ("Kekik", "kuru kekik"),
    "Reyhan": ("Reyhan", "kuru reyhan"),
    "Yag": ("Yağ", "yag,ayçiçek yağı,aycicek yagi,sıvı yağ,sivi yag"),
    "Cay": ("Çay", "cay,siyah çay,siyah cay,rize çayı,rize cayi"),
    "Sabun": ("Sabun", "zeytinyağlı sabun,zeytinyagli sabun"),
    "Kolonya": ("Kolonya", "limon kolonyası,limon kolonyasi"),
}


async def run() -> None:
    async with SessionLocal() as db:
        res = await db.execute(select(Product))
        products = list(res.scalars())
        by_normalized_name = {normalize_text(p.name): p for p in products}

        updated = 0
        for old_name, (new_name, aliases) in PRODUCT_NAME_UPDATES.items():
            product = by_normalized_name.get(normalize_text(old_name))
            if not product:
                # Ürün zaten Türkçe adla güncellenmiş olabilir.
                product = by_normalized_name.get(normalize_text(new_name))
            if not product:
                continue
            product.name = new_name
            product.aliases = aliases
            updated += 1

        await db.commit()
    print(f"Product names normalized: {updated} products updated")


if __name__ == "__main__":
    asyncio.run(run())
