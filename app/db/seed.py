"""Gercekci demo verisi uretici. `python -m app.db.seed --clear --demo-fixtures` ile calistir."""

import argparse
import asyncio
import random
import string
from datetime import date, datetime, timedelta

from sqlalchemy import delete, text

from app.db.models import (
    Customer,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    Shipment,
    ShipmentStatus,
    TelegramSession,
)
from app.db.session import SessionLocal
from app.integrations.cargo_mock import CARRIERS, LOCATIONS

PRODUCT_CATALOG = [
    ("Bal", "çiçek balı,cicek bali,süzme bal,suzme bal,doğal bal,dogal bal", "kg", 280.0, 8.0, 10.0, "Cam kavanozda doğal çiçek balı"),
    ("Zeytinyağı", "zeytinyagi,zeytin yağı,zeytin yagi,naturel sızma,naturel sizma", "lt", 320.0, 25.0, 10.0, "Erken hasat"),
    ("Domates", "salkım domates,salkim domates,kuru domates", "kg", 18.0, 50.0, 30.0, "Yerli salkım"),
    ("Biber", "yeşil biber,yesil biber,sivri biber", "kg", 22.0, 30.0, 15.0, "Sivri yeşil biber"),
    ("Salça", "salca,domates salçası,domates salcasi,biber salçası,biber salcasi", "kg", 75.0, 40.0, 15.0, "Ev yapımı salça"),
    ("Reçel", "recel,kayısı reçeli,kayisi receli,vişne reçeli,visne receli", "kg", 110.0, 18.0, 10.0, "Şekersiz alternatif mevcut"),
    ("Peynir", "beyaz peynir,kaşar,kasar", "kg", 240.0, 22.0, 10.0, "Tam yağlı inek peyniri"),
    ("Yoğurt", "yogurt,süzme yoğurt,suzme yogurt,kaymaklı,kaymakli", "kg", 60.0, 35.0, 15.0, "Tam yağlı"),
    ("Tereyağı", "tereyagi,köy tereyağı,koy tereyagi,tuzsuz tereyağı,tuzsuz tereyagi", "kg", 380.0, 12.0, 8.0, "Tuzsuz"),
    ("Yumurta", "köy yumurtası,koy yumurtasi,gezen tavuk yumurtası,gezen tavuk yumurtasi", "adet", 7.0, 200.0, 60.0, "Gezen tavuk"),
    ("Un", "tam buğday unu,tam bugday unu", "kg", 25.0, 60.0, 30.0, "Tam buğday"),
    ("Bulgur", "kepekli bulgur,pilavlık bulgur,pilavlik bulgur", "kg", 35.0, 40.0, 20.0, "Pilavlık"),
    ("Mercimek", "kırmızı mercimek,kirmizi mercimek,yeşil mercimek,yesil mercimek", "kg", 45.0, 35.0, 15.0, "Yerli"),
    ("Nohut", "iri nohut", "kg", 40.0, 30.0, 15.0, ""),
    ("Fasulye", "kuru fasulye,ispir fasulyesi", "kg", 80.0, 25.0, 12.0, "İspir tipi"),
    ("Pirinç", "pirinc,baldo pirinç,baldo pirinc", "kg", 55.0, 40.0, 15.0, ""),
    ("Ceviz", "iç ceviz,ic ceviz", "kg", 320.0, 14.0, 6.0, "Yeni hasat"),
    ("Fındık", "findik,iç fındık,ic findik", "kg", 380.0, 10.0, 5.0, ""),
    ("Kuru Üzüm", "kuru uzum,üzüm,uzum,sultaniye", "kg", 95.0, 18.0, 8.0, ""),
    ("Kuru İncir", "kuru incir,incir", "kg", 180.0, 12.0, 5.0, ""),
    ("Pekmez", "üzüm pekmezi,uzum pekmezi,dut pekmezi", "kg", 130.0, 20.0, 10.0, ""),
    ("Tarhana", "ev tarhanası,ev tarhanasi", "kg", 95.0, 14.0, 6.0, ""),
    ("Sirke", "üzüm sirkesi,uzum sirkesi,elma sirkesi", "lt", 65.0, 25.0, 10.0, ""),
    ("Susam Yağı", "susam yagi,susam yağı,tahin", "kg", 220.0, 18.0, 8.0, ""),
    ("Kekik", "kuru kekik", "kg", 280.0, 5.0, 2.0, ""),
    ("Reyhan", "kuru reyhan", "kg", 240.0, 4.0, 2.0, ""),
    ("Yağ", "yag,ayçiçek yağı,aycicek yagi,sıvı yağ,sivi yag", "lt", 95.0, 30.0, 12.0, ""),
    ("Çay", "cay,siyah çay,siyah cay,rize çayı,rize cayi", "kg", 280.0, 20.0, 10.0, "Rize"),
    ("Sabun", "zeytinyağlı sabun,zeytinyagli sabun", "adet", 35.0, 80.0, 30.0, ""),
    ("Kolonya", "limon kolonyası,limon kolonyasi", "lt", 110.0, 20.0, 8.0, ""),
]

CUSTOMER_NAMES = [
    "Ayse Yilmaz", "Mehmet Kaya", "Fatma Demir", "Ahmet Sahin", "Zeynep Celik",
    "Mustafa Aydin", "Elif Ozdemir", "Ali Arslan", "Hatice Dogan", "Hasan Polat",
    "Emine Koc", "Huseyin Kurt", "Sevim Aksoy", "Murat Yildiz", "Esra Erdogan",
    "Ibrahim Cetin", "Sevgi Avci", "Yusuf Aslan", "Merve Ozturk", "Burak Sarac",
    "Selin Demirci", "Eren Bulut", "Pinar Ozkan", "Cem Gunes", "Aysegul Tasdemir",
    "Onur Erdem", "Gulsah Kara", "Tolga Karatas", "Berk Akin", "Sinem Atalay",
    "Caner Sevinc", "Ozlem Erol", "Furkan Acar", "Beyza Coskun", "Kaan Yalcin",
    "Defne Cetinkaya", "Tuna Saglam", "Ipek Yildirim", "Baris Tunc", "Selma Korkmaz",
    "Berkay Cinar", "Ece Uzun", "Volkan Sezer", "Aleyna Bayrak", "Cihan Demirel",
    "Gozde Soylu", "Emre Pamuk", "Cansu Akar", "Sercan Erkan", "Asya Cakir",
]

random.seed(42)


def _tracking_no() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TR{suffix}"


async def clear_all(db) -> None:
    """Demo verisini temizler ve id sayaçlarını sıfırlar.

    Önceki sürüm DELETE kullandığı için PostgreSQL sequence değerleri artmaya
    devam ediyordu. Birkaç kez seed çalıştırınca müşteri id'leri 101, 151 gibi
    değerlere kayıyor; eski frontend linkleri de 404 üretebiliyordu.
    """
    await db.execute(
        text(
            "TRUNCATE TABLE shipments, order_items, orders, products, "
            "customers, telegram_sessions RESTART IDENTITY CASCADE"
        )
    )
    await db.commit()


async def seed_products(db) -> list[Product]:
    products = []
    for name, aliases, unit, price, stock, threshold, desc in PRODUCT_CATALOG:
        p = Product(
            name=name,
            aliases=aliases or None,
            unit=unit,
            price=price,
            stock=stock,
            low_stock_threshold=threshold,
            description=desc or None,
        )
        db.add(p)
        products.append(p)
    await db.flush()
    return products


async def seed_customers(db) -> list[Customer]:
    customers = []
    for i, name in enumerate(CUSTOMER_NAMES):
        phone = f"+9055{random.randint(10000000, 99999999)}"
        tg_id = (10000 + i) if i < len(CUSTOMER_NAMES) // 2 else None
        c = Customer(name=name, phone=phone, telegram_user_id=tg_id)
        db.add(c)
        customers.append(c)
    await db.flush()
    return customers


async def _add_items(db, order: Order, item_list: list[tuple[Product, float]]) -> None:
    for p, q in item_list:
        db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=q, unit_price=p.price))
    await db.flush()


async def _add_shipment(
    db,
    order: Order,
    *,
    status: ShipmentStatus,
    carrier: str | None = None,
    last_event_at: datetime | None = None,
    estimated_delivery: date | None = None,
    location: str | None = None,
) -> Shipment:
    shipment = Shipment(
        order_id=order.id,
        tracking_no=_tracking_no(),
        carrier=carrier or random.choice(CARRIERS),
        status=status,
        last_event_at=last_event_at or datetime.utcnow(),
        estimated_delivery=estimated_delivery or order.promised_delivery,
        current_location=location or ("Teslim edildi" if status == ShipmentStatus.DELIVERED else random.choice(LOCATIONS)),
    )
    db.add(shipment)
    await db.flush()
    return shipment


async def _create_order(
    db,
    *,
    customer: Customer,
    items: list[tuple[Product, float]],
    status: OrderStatus,
    created_at: datetime,
    promised_delivery: date | None = None,
    order_id: int | None = None,
    note: str | None = None,
) -> Order:
    total = round(sum(p.price * q for p, q in items), 2)
    kwargs = {}
    if order_id is not None:
        kwargs["id"] = order_id
    order = Order(
        **kwargs,
        customer_id=customer.id,
        status=status,
        total=total,
        created_at=created_at,
        promised_delivery=promised_delivery or (created_at + timedelta(days=random.randint(2, 4))).date(),
        note=note,
    )
    db.add(order)
    await db.flush()
    await _add_items(db, order, items)
    return order


async def seed_orders(db, customers: list[Customer], products: list[Product], total: int = 200):
    """Gecmis siparisleri gercekci dagitir.

    Eski siparisler cogunlukla teslim edildi olur. Bekleyen/hazirlanan siparisler son birkac gune aittir.
    Bu sayede demo ekraninda 3 ay once hazirlanmis siparis gibi mantiksiz kayitlar gorunmez.
    """
    now = datetime.utcnow()
    status_pool = (
        [OrderStatus.DELIVERED] * 145
        + [OrderStatus.SHIPPED] * 18
        + [OrderStatus.PREPARED] * 18
        + [OrderStatus.PENDING] * 14
        + [OrderStatus.CANCELLED] * 5
    )

    for _ in range(total):
        c = random.choice(customers)
        chosen = random.sample(products, random.randint(1, 4))
        items = []
        for p in chosen:
            qty = round(random.uniform(0.5, 5.0), 1) if p.unit != "adet" else random.randint(1, 10)
            items.append((p, float(qty)))

        status = random.choice(status_pool)
        if status == OrderStatus.DELIVERED:
            days_ago = random.randint(5, 75)
        elif status in (OrderStatus.SHIPPED, OrderStatus.PREPARED, OrderStatus.PENDING):
            days_ago = random.randint(0, 4)
        else:
            days_ago = random.randint(2, 60)

        created = now - timedelta(days=days_ago, hours=random.randint(0, 20))
        promised = (created + timedelta(days=random.randint(2, 4))).date()
        order = await _create_order(
            db,
            customer=c,
            items=items,
            status=status,
            created_at=created,
            promised_delivery=promised,
        )

        if status == OrderStatus.DELIVERED:
            delivered_at = created + timedelta(days=random.randint(1, 4), hours=random.randint(1, 8))
            if delivered_at > now:
                delivered_at = now - timedelta(hours=random.randint(2, 12))
            await _add_shipment(
                db,
                order,
                status=ShipmentStatus.DELIVERED,
                last_event_at=delivered_at,
                estimated_delivery=promised,
                location="Teslim edildi",
            )
        elif status == OrderStatus.SHIPPED:
            ship_status = random.choice([
                ShipmentStatus.PICKED_UP,
                ShipmentStatus.IN_TRANSIT,
                ShipmentStatus.OUT_FOR_DELIVERY,
            ])
            await _add_shipment(
                db,
                order,
                status=ship_status,
                last_event_at=now - timedelta(hours=random.randint(2, 30)),
                estimated_delivery=max(promised, (now + timedelta(days=random.randint(1, 2))).date()),
            )
    await db.flush()


async def apply_demo_fixtures(db, customers: list[Customer], products: list[Product]):
    """Demo senaryolari icin sabit ve kontrollu veri."""
    now = datetime.utcnow()
    ayse = next((c for c in customers if c.name == "Ayse Yilmaz"), None)
    if not ayse:
        ayse = Customer(name="Ayse Yilmaz", phone="+905550000128", telegram_user_id=99999)
        db.add(ayse)
        await db.flush()
    else:
        ayse.telegram_user_id = 99999

    bal = next(p for p in products if p.name == "Bal")
    zeytin = next(p for p in products if p.name == "Zeytinyağı")
    domates = next(p for p in products if p.name == "Domates")
    recel = next(p for p in products if p.name == "Reçel")

    # Sadece Bal kritik stokta kalsin; digerleri normal gorunsun.
    bal.stock = 8.0
    domates.stock = 50.0
    recel.stock = 18.0

    # Ayse Yilmaz icin temiz ve anlasilir siparis gecmisi.
    ayse_orders = [
        (now - timedelta(days=26), [(bal, 2.0), (zeytin, 1.0)]),
        (now - timedelta(days=18), [(recel, 2.0)]),
        (now - timedelta(days=10), [(zeytin, 2.0), (domates, 3.0)]),
    ]
    for created, item_list in ayse_orders:
        order = await _create_order(
            db,
            customer=ayse,
            items=item_list,
            status=OrderStatus.DELIVERED,
            created_at=created,
            promised_delivery=(created + timedelta(days=3)).date(),
        )
        await _add_shipment(
            db,
            order,
            status=ShipmentStatus.DELIVERED,
            last_event_at=created + timedelta(days=2, hours=5),
            estimated_delivery=(created + timedelta(days=3)).date(),
            location="Teslim edildi",
        )

    target_id = 128
    existing = await db.get(Order, target_id)
    if existing:
        await db.execute(delete(Shipment).where(Shipment.order_id == target_id))
        await db.execute(delete(OrderItem).where(OrderItem.order_id == target_id))
        await db.delete(existing)
        await db.flush()

    order_128 = await _create_order(
        db,
        order_id=target_id,
        customer=ayse,
        items=[(bal, 2.0), (zeytin, 1.0)],
        status=OrderStatus.SHIPPED,
        created_at=now - timedelta(days=2, hours=2),
        promised_delivery=date.today() + timedelta(days=1),
        note="Demo siparis: musteri kargo durumunu soracak.",
    )
    await _add_shipment(
        db,
        order_128,
        status=ShipmentStatus.IN_TRANSIT,
        carrier="Marmara Kurye",
        last_event_at=now - timedelta(hours=5),
        estimated_delivery=date.today() + timedelta(days=1),
        location="İstanbul Anadolu Şubesi",
    )

    # Kargo risk ekraninda makul sayida problemli kayit gorunsun diye 3 gecikmis kargo.
    risk_customers = [c for c in customers if c.id != ayse.id][:3]
    for idx, customer in enumerate(risk_customers):
        created = now - timedelta(days=6 + idx)
        product = random.choice(products)
        order = await _create_order(
            db,
            customer=customer,
            items=[(product, 1.0)],
            status=OrderStatus.SHIPPED,
            created_at=created,
            promised_delivery=(date.today() - timedelta(days=1 + idx)),
            note="Demo gecikme riski",
        )
        await _add_shipment(
            db,
            order,
            status=ShipmentStatus.IN_TRANSIT,
            carrier=random.choice(["Anadolu Kargo", "Koop Lojistik"]),
            last_event_at=now - timedelta(days=2, hours=idx),
            estimated_delivery=date.today() - timedelta(days=1 + idx),
            location=random.choice(LOCATIONS),
        )

    await db.execute(text("SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders))"))


async def run(demo_fixtures: bool, clear: bool):
    async with SessionLocal() as db:
        if clear:
            await clear_all(db)
        products = await seed_products(db)
        customers = await seed_customers(db)
        await seed_orders(db, customers, products, total=200)
        if demo_fixtures:
            await apply_demo_fixtures(db, customers, products)
        await db.commit()
    print(
        f"Seed complete: {len(PRODUCT_CATALOG)} products, "
        f"{len(CUSTOMER_NAMES)} customers, 200+ realistic orders"
    )
    if demo_fixtures:
        print("Demo fixtures applied: Ayse Yilmaz, Order #128, realistic cargo risks")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-fixtures", action="store_true")
    parser.add_argument("--clear", action="store_true", help="Mevcut veriyi temizle")
    args = parser.parse_args()
    asyncio.run(run(args.demo_fixtures, args.clear))


if __name__ == "__main__":
    main()
