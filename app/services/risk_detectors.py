"""Proaktif risk gozcusu — sistem verisinde anomali tespit eden finder'lar.

Deterministik (LLM yok): SQL sorgulariyla risk taşıyan kayıtlari bulur.
Cikti: her finder bir liste dict doner; agent bu listeleri tarayip
subject+description yazar ve CustomerComplaint olarak kaydeder.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Customer,
    CustomerComplaint,
    Order,
    OrderItem,
    OrderStatus,
    Shipment,
    ShipmentStatus,
)


async def find_delayed_shipments(
    db: AsyncSession, today: date | None = None
) -> list[dict]:
    """estimated_delivery tarihi gecmis ve hala DELIVERED olmamis kargolar.

    Cikti: [{shipment_id, order_id, customer_id, customer_name,
             tracking_no, days_overdue, expected_date}]
    """
    today = today or date.today()
    res = await db.execute(
        select(Shipment)
        .where(
            Shipment.estimated_delivery.is_not(None),
            Shipment.estimated_delivery < today,
            Shipment.status != ShipmentStatus.DELIVERED,
        )
        .options(
            selectinload(Shipment.order).selectinload(Order.customer)
        )
        .order_by(Shipment.estimated_delivery.asc())
    )
    out = []
    for s in res.scalars():
        if not s.order:
            continue
        days_overdue = (today - s.estimated_delivery).days
        cust = s.order.customer
        out.append(
            {
                "shipment_id": s.id,
                "order_id": s.order_id,
                "customer_id": cust.id if cust else None,
                "customer_name": cust.name if cust else None,
                "tracking_no": s.tracking_no,
                "carrier": s.carrier,
                "current_status": s.status.value,
                "current_location": s.current_location,
                "days_overdue": days_overdue,
                "expected_date": s.estimated_delivery.isoformat(),
            }
        )
    return out


async def find_slow_shipments(
    db: AsyncSession, std_multiplier: float = 2.0
) -> list[dict]:
    """Aktif kargolar arasında ortalama+std×N kadar yaşlı olanlar.

    Mantık: shipment.created_at (last_event_at proxy) bugüne göre yaş hesaplar;
    sistem ortalamasının std×N üstündekiler "yavaş" sayılır.
    Sadece DELIVERED OLMAYANLAR.
    """
    res = await db.execute(
        select(Shipment)
        .where(Shipment.status != ShipmentStatus.DELIVERED)
        .options(selectinload(Shipment.order).selectinload(Order.customer))
    )
    actives = list(res.scalars())
    if len(actives) < 3:
        return []  # Anlamlı bir ortalama hesabı için en az 3 örnek
    now = datetime.utcnow()
    ages = [(now - s.last_event_at).total_seconds() / 86400 for s in actives]
    mean = sum(ages) / len(ages)
    var = sum((a - mean) ** 2 for a in ages) / len(ages)
    std = var**0.5
    threshold = mean + std_multiplier * std
    out = []
    for s, age in zip(actives, ages):
        if age <= threshold or age <= mean + 0.5:
            continue
        # Delayed shipments ile cakismayi engelle: estimated_delivery hala
        # gelecekteyse yavas kategorisinde yer almasin
        if (
            s.estimated_delivery
            and s.estimated_delivery < date.today()
        ):
            continue
        cust = s.order.customer if s.order else None
        out.append(
            {
                "shipment_id": s.id,
                "order_id": s.order_id,
                "customer_id": cust.id if cust else None,
                "customer_name": cust.name if cust else None,
                "tracking_no": s.tracking_no,
                "current_status": s.status.value,
                "age_days": round(age, 1),
                "avg_age_days": round(mean, 1),
                "threshold_days": round(threshold, 1),
            }
        )
    return out


async def find_stale_pending_orders(
    db: AsyncSession, hours_threshold: int = 24
) -> list[dict]:
    """PENDING durumunda hours_threshold+ saat takılı kalmış siparişler."""
    cutoff = datetime.utcnow() - timedelta(hours=hours_threshold)
    res = await db.execute(
        select(Order)
        .where(
            Order.status == OrderStatus.PENDING,
            Order.created_at <= cutoff,
        )
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.asc())
    )
    now = datetime.utcnow()
    out = []
    for o in res.scalars():
        hours_pending = int((now - o.created_at).total_seconds() / 3600)
        items_summary = ", ".join(
            f"{i.quantity} {i.product.unit if i.product else ''} "
            f"{i.product.name if i.product else '?'}"
            for i in (o.items or [])[:3]
        )
        out.append(
            {
                "order_id": o.id,
                "customer_id": o.customer.id if o.customer else None,
                "customer_name": o.customer.name if o.customer else None,
                "total": float(o.total),
                "hours_pending": hours_pending,
                "items_summary": items_summary,
                "created_at": o.created_at.isoformat(),
            }
        )
    return out


async def find_repeat_complainers(
    db: AsyncSession, min_count: int = 2, since_days: int = 30
) -> list[dict]:
    """Son N gunde birden fazla acik sikayeti olan musteriler."""
    since = datetime.utcnow() - timedelta(days=since_days)
    res = await db.execute(
        select(
            CustomerComplaint.customer_id,
            func.count(CustomerComplaint.id).label("n"),
            func.max(CustomerComplaint.risk_score).label("max_risk"),
            func.max(CustomerComplaint.created_at).label("last_at"),
        )
        .where(
            CustomerComplaint.customer_id.is_not(None),
            CustomerComplaint.created_at >= since,
        )
        .group_by(CustomerComplaint.customer_id)
        .having(func.count(CustomerComplaint.id) >= min_count)
    )
    rows = res.all()
    out = []
    for r in rows:
        cust = await db.get(Customer, r.customer_id)
        out.append(
            {
                "customer_id": r.customer_id,
                "customer_name": cust.name if cust else None,
                "complaint_count": int(r.n),
                "max_risk_score": float(r.max_risk or 0),
                "last_complaint_at": r.last_at.isoformat() if r.last_at else None,
                "since_days": since_days,
            }
        )
    return out


async def find_dormant_customers(
    db: AsyncSession, days_silent: int = 60, min_prior_orders: int = 3
) -> list[dict]:
    """Düzenli (en az 3 önceki sipariş) ama days_silent gündür hareketsiz musteriler."""
    cutoff = datetime.utcnow() - timedelta(days=days_silent)
    # Önce her müşterinin toplam sipariş sayısını ve son sipariş tarihini al
    res = await db.execute(
        select(
            Order.customer_id,
            func.count(Order.id).label("n"),
            func.max(Order.created_at).label("last_at"),
            func.sum(Order.total).label("total_spend"),
        )
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(Order.customer_id)
        .having(func.count(Order.id) >= min_prior_orders)
    )
    out = []
    for r in res.all():
        if not r.last_at or r.last_at >= cutoff:
            continue
        cust = await db.get(Customer, r.customer_id)
        days_silent_actual = (datetime.utcnow() - r.last_at).days
        out.append(
            {
                "customer_id": r.customer_id,
                "customer_name": cust.name if cust else None,
                "prior_order_count": int(r.n),
                "total_spend": round(float(r.total_spend or 0), 2),
                "days_silent": days_silent_actual,
                "last_order_at": r.last_at.isoformat(),
            }
        )
    out.sort(key=lambda x: x["days_silent"], reverse=True)
    return out
