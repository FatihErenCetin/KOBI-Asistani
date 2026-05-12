"""Demo verisi uretici. `python -m app.db.seed --demo-fixtures` ile calistir."""

import argparse
import asyncio
import random
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
from app.integrations import cargo_mock

PRODUCT_CATALOG = [
    ("Bal", "cicek bali,suzme bal", "kg", 280.0, 8.0, 10.0, "Cam kavanozda dogal cicek bali"),
    ("Zeytinyagi", "zeytin yagi,naturel sizma", "lt", 320.0, 25.0, 10.0, "Erken hasat"),
    ("Domates", "salkim domates,kuru domates", "kg", 18.0, 50.0, 30.0, "Yerli salkim"),
    ("Biber", "yesil biber,sivri biber", "kg", 22.0, 30.0, 15.0, "Sivri yesil biber"),
    ("Salca", "domates salcasi,biber salcasi", "kg", 75.0, 40.0, 15.0, "Ev yapimi salca"),
    ("Recel", "kayisi receli,visne receli", "kg", 110.0, 18.0, 10.0, "Sekersiz alternatif mevcut"),
    ("Peynir", "beyaz peynir,kasar", "kg", 240.0, 22.0, 10.0, "Tam yagli inek"),
    ("Yogurt", "suzme yogurt,kaymakli", "kg", 60.0, 35.0, 15.0, "Tam yagli"),
    ("Tereyagi", "koy tereyagi", "kg", 380.0, 12.0, 8.0, "Tuzsuz"),
    ("Yumurta", "koy yumurtasi", "adet", 7.0, 200.0, 60.0, "Gezen tavuk"),
    ("Un", "tam bugday unu", "kg", 25.0, 60.0, 30.0, "Tam bugday"),
    ("Bulgur", "kepekli bulgur", "kg", 35.0, 40.0, 20.0, "Pilavlik"),
    ("Mercimek", "kirmizi mercimek,yesil mercimek", "kg", 45.0, 35.0, 15.0, "Yerli"),
    ("Nohut", "iri nohut", "kg", 40.0, 30.0, 15.0, ""),
    ("Fasulye", "kuru fasulye", "kg", 80.0, 25.0, 12.0, "Ispir tipi"),
    ("Pirinc", "baldo pirinc", "kg", 55.0, 40.0, 15.0, ""),
    ("Ceviz", "ic ceviz", "kg", 320.0, 14.0, 6.0, "Yeni hasat"),
    ("Findik", "ic findik", "kg", 380.0, 10.0, 5.0, ""),
    ("Kuru Uzum", "sultaniye", "kg", 95.0, 18.0, 8.0, ""),
    ("Kuru Incir", "kuru incir", "kg", 180.0, 12.0, 5.0, ""),
    ("Pekmez", "uzum pekmezi,dut pekmezi", "kg", 130.0, 20.0, 10.0, ""),
    ("Tarhana", "ev tarhanasi", "kg", 95.0, 14.0, 6.0, ""),
    ("Sirke", "uzum sirkesi,elma sirkesi", "lt", 65.0, 25.0, 10.0, ""),
    ("Susam Yagi", "tahin", "kg", 220.0, 18.0, 8.0, ""),
    ("Kekik", "kuru kekik", "kg", 280.0, 5.0, 2.0, ""),
    ("Reyhan", "kuru reyhan", "kg", 240.0, 4.0, 2.0, ""),
    ("Yag", "ayciceg yagi", "lt", 95.0, 30.0, 12.0, ""),
    ("Cay", "siyah cay", "kg", 280.0, 20.0, 10.0, "Rize"),
    ("Sabun", "zeytinyagli sabun", "adet", 35.0, 80.0, 30.0, ""),
    ("Kolonya", "limon kolonyasi", "lt", 110.0, 20.0, 8.0, ""),
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


async def clear_all(db) -> None:
    for model in [Shipment, OrderItem, Order, Product, Customer, TelegramSession]:
        await db.execute(delete(model))
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


async def seed_orders(db, customers: list[Customer], products: list[Product], total: int = 200):
    now = datetime.utcnow()
    status_dist = (
        [OrderStatus.DELIVERED] * 60
        + [OrderStatus.SHIPPED] * 15
        + [OrderStatus.PREPARED] * 15
        + [OrderStatus.PENDING] * 10
    )
    for _ in range(total):
        c = random.choice(customers)
        n_items = random.randint(1, 5)
        chosen = random.sample(products, n_items)
        items = []
        order_total = 0.0
        for p in chosen:
            qty = (
                round(random.uniform(0.5, 5.0), 1)
                if p.unit != "adet"
                else random.randint(1, 10)
            )
            items.append((p, float(qty)))
            order_total += p.price * qty
        days_ago = random.randint(0, 89)
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        status = random.choice(status_dist)
        order = Order(
            customer_id=c.id,
            status=status,
            total=round(order_total, 2),
            created_at=created,
            promised_delivery=(created + timedelta(days=random.randint(1, 5))).date(),
        )
        db.add(order)
        await db.flush()
        for p, qty in items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    quantity=qty,
                    unit_price=p.price,
                )
            )
        if status == OrderStatus.SHIPPED:
            shipment = await cargo_mock.create_shipment(db, order)
            advance_count = random.randint(1, 3)
            for _ in range(advance_count):
                await cargo_mock.advance(db, shipment)
            if shipment.status == ShipmentStatus.DELIVERED:
                shipment.status = ShipmentStatus.OUT_FOR_DELIVERY
                order.status = OrderStatus.SHIPPED
    await db.flush()


async def apply_demo_fixtures(db, customers: list[Customer], products: list[Product]):
    """Demo senaryolari icin sabit veri."""
    ayse = next((c for c in customers if c.name == "Ayse Yilmaz"), None)
    if not ayse:
        ayse = Customer(name="Ayse Yilmaz", phone="+905550000128", telegram_user_id=99999)
        db.add(ayse)
        await db.flush()
    else:
        ayse.telegram_user_id = 99999

    bal = next(p for p in products if p.name == "Bal")
    zeytin = next(p for p in products if p.name == "Zeytinyagi")
    domates = next(p for p in products if p.name == "Domates")

    bal.stock = 8.0
    domates.stock = 49.0

    base_date = datetime.utcnow() - timedelta(days=30)
    fixture_orders = [
        (base_date + timedelta(days=5), [(bal, 2.0), (zeytin, 1.0)], OrderStatus.DELIVERED),
        (base_date + timedelta(days=12), [(bal, 1.5)], OrderStatus.DELIVERED),
        (base_date + timedelta(days=20), [(zeytin, 2.0), (domates, 3.0)], OrderStatus.DELIVERED),
    ]
    for created, item_list, status in fixture_orders:
        total = sum(p.price * q for p, q in item_list)
        order = Order(
            customer_id=ayse.id,
            status=status,
            total=round(total, 2),
            created_at=created,
            promised_delivery=(created + timedelta(days=2)).date(),
        )
        db.add(order)
        await db.flush()
        for p, q in item_list:
            db.add(
                OrderItem(order_id=order.id, product_id=p.id, quantity=q, unit_price=p.price)
            )

    target_id = 128
    existing = await db.get(Order, target_id)
    if existing:
        # iliskili shipment/items'i da sileceğiz
        await db.execute(delete(Shipment).where(Shipment.order_id == target_id))
        await db.execute(delete(OrderItem).where(OrderItem.order_id == target_id))
        await db.delete(existing)
        await db.flush()
    order_128 = Order(
        id=target_id,
        customer_id=ayse.id,
        status=OrderStatus.SHIPPED,
        total=round(bal.price * 2 + zeytin.price * 1, 2),
        created_at=datetime.utcnow() - timedelta(days=2),
        promised_delivery=date.today() + timedelta(days=1),
    )
    db.add(order_128)
    await db.flush()
    db.add(OrderItem(order_id=order_128.id, product_id=bal.id, quantity=2.0, unit_price=bal.price))
    db.add(
        OrderItem(
            order_id=order_128.id, product_id=zeytin.id, quantity=1.0, unit_price=zeytin.price
        )
    )
    await db.flush()
    shipment = await cargo_mock.create_shipment(db, order_128)
    shipment.status = ShipmentStatus.IN_TRANSIT
    shipment.current_location = "Istanbul Anadolu Subesi"
    shipment.estimated_delivery = date.today() + timedelta(days=1)
    await db.flush()

    # Postgres sequence sync: explicit id=128 sequence'i ilerletmedi
    await db.execute(
        text("SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders))")
    )


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
        f"{len(CUSTOMER_NAMES)} customers, 200+ orders"
    )
    if demo_fixtures:
        print("Demo fixtures applied: Ayse Yilmaz (tg=99999), Order #128 SHIPPED IN_TRANSIT")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo-fixtures", action="store_true")
    parser.add_argument("--clear", action="store_true", help="Mevcut veriyi temizle")
    args = parser.parse_args()
    asyncio.run(run(args.demo_fixtures, args.clear))


if __name__ == "__main__":
    main()
