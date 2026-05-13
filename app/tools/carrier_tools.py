"""Kargo firma performans analizi."""

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Order, OrderItem, Shipment, ShipmentStatus
from app.tools.base import AgentContext


def _days_between(dt1: datetime, dt2: datetime) -> float:
    return max(0.0, (dt2 - dt1).total_seconds() / 86400)


def _risk_level(score: float) -> str:
    if score >= 30:
        return "high"
    if score >= 12:
        return "medium"
    return "low"


async def carrier_performance_analysis(*, since_days: int = 30, ctx: AgentContext) -> dict:
    """Kargo firma bazinda performans analizi yapar."""
    if not ctx.is_admin:
        return {"error": "Yetki yok."}

    since = datetime.utcnow() - timedelta(days=since_days)
    res = await ctx.db.execute(
        select(Shipment)
        .join(Shipment.order)
        .where(Order.created_at >= since)
        .options(
            selectinload(Shipment.order).selectinload(Order.customer),
            selectinload(Shipment.order).selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    shipments = list(res.scalars())

    carrier_stats: dict = defaultdict(lambda: {
        "total": 0,
        "delivered": 0,
        "delayed": 0,
        "stale": 0,
        "delivery_days": [],
        "complaint_risk": [],
    })

    now = datetime.utcnow()
    stale_threshold = now - timedelta(hours=48)

    for s in shipments:
        order = s.order
        if order is None:
            continue

        carrier = s.carrier or "Bilinmiyor"
        stats = carrier_stats[carrier]
        stats["total"] += 1

        if s.status == ShipmentStatus.DELIVERED:
            stats["delivered"] += 1
            stats["delivery_days"].append(round(_days_between(order.created_at, s.last_event_at), 1))
            continue

        days_late = 0
        if order.promised_delivery and order.promised_delivery < now.date():
            days_late = (now.date() - order.promised_delivery).days
            stats["delayed"] += 1

        is_stale = s.status in (ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY) and s.last_event_at < stale_threshold
        if is_stale:
            stats["stale"] += 1

        if days_late > 0 or is_stale:
            customer_name = order.customer.name if order.customer else "-"
            stats["complaint_risk"].append({
                "order_id": order.id,
                "customer": customer_name,
                "tracking": s.tracking_no,
                "promised": order.promised_delivery.isoformat() if order.promised_delivery else None,
                "days_late": days_late,
                "status": s.status.value,
                "location": s.current_location,
            })

    carriers = []
    for carrier, stats in carrier_stats.items():
        total = stats["total"]
        delivered = stats["delivered"]
        delayed = stats["delayed"]
        stale = stats["stale"]
        avg_days = round(sum(stats["delivery_days"]) / len(stats["delivery_days"]), 1) if stats["delivery_days"] else None
        delay_rate = round(delayed / total * 100, 1) if total else 0
        delivery_rate = round(delivered / total * 100, 1) if total else 0
        stale_rate = stale / total * 100 if total else 0
        risk_score = round((delay_rate * 0.75) + (stale_rate * 0.25), 1)

        carriers.append({
            "carrier": carrier,
            "total_shipments": total,
            "delivered": delivered,
            "delivery_rate_pct": delivery_rate,
            "delayed": delayed,
            "delay_rate_pct": delay_rate,
            "stale_shipments": stale,
            "avg_delivery_days": avg_days,
            "risk_score": risk_score,
            "risk_level": _risk_level(risk_score),
            "top_complaint_risks": sorted(
                stats["complaint_risk"], key=lambda x: (x["days_late"], x["order_id"]), reverse=True
            )[:5],
        })

    carriers.sort(key=lambda x: x["risk_score"], reverse=True)

    total_all = sum(c["total_shipments"] for c in carriers)
    total_delayed = sum(c["delayed"] for c in carriers)
    worst = carriers[0] if carriers else None
    best = sorted(carriers, key=lambda x: (x["risk_score"], -x["delivery_rate_pct"]))[0] if carriers else None

    if not carriers:
        recommendation = "Son 30 gün için kargo kaydı bulunamadı."
    elif worst and worst["delay_rate_pct"] >= 25:
        recommendation = f"{worst['carrier']} tarafında gecikme oranı %{worst['delay_rate_pct']}. Bu firma için operasyon takibi artırılmalı."
    elif worst and worst["delay_rate_pct"] >= 10:
        recommendation = f"Genel performans kabul edilebilir; sadece {worst['carrier']} için gecikme riski izlenmeli."
    else:
        recommendation = "Kargo firmalarının genel performansı dengeli görünüyor. Kritik bir gecikme yoğunluğu yok."

    return {
        "period_days": since_days,
        "total_shipments": total_all,
        "total_delayed": total_delayed,
        "overall_delay_rate_pct": round(total_delayed / total_all * 100, 1) if total_all else 0,
        "carriers": carriers,
        "worst_carrier": worst["carrier"] if worst else None,
        "best_carrier": best["carrier"] if best else None,
        "recommendation": recommendation,
    }


async def high_complaint_risk_orders(*, ctx: AgentContext) -> dict:
    """Sikayet riski en yuksek siparisleri listeler."""
    if not ctx.is_admin:
        return {"error": "Yetki yok."}

    result = await carrier_performance_analysis(since_days=30, ctx=ctx)
    if "error" in result:
        return result

    all_risks = []
    for carrier_data in result["carriers"]:
        for risk in carrier_data["top_complaint_risks"]:
            all_risks.append({**risk, "carrier": carrier_data["carrier"]})

    all_risks.sort(key=lambda x: (x["days_late"], x["order_id"]), reverse=True)
    return {"count": len(all_risks), "orders": all_risks[:10]}
