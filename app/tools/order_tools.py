import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.models import OrderStatus, TelegramSession
from app.tools.base import AgentContext


def _format_order(order) -> dict:
    return {
        "order_id": order.id,
        "status": order.status.value,
        "total": float(order.total),
        "created_at": order.created_at.isoformat(),
        "promised_delivery": (
            order.promised_delivery.isoformat() if order.promised_delivery else None
        ),
        "items": [
            {
                "product": item.product.name if item.product else None,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order.items
        ],
        "shipment": _format_shipment(order.shipment) if order.shipment else None,
        "customer_name": order.customer.name if order.customer else None,
    }


def _format_shipment(s) -> dict:
    return {
        "tracking_no": s.tracking_no,
        "carrier": s.carrier,
        "status": s.status.value,
        "location": s.current_location,
        "eta": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
    }


async def get_my_order_status(order_id: int, *, ctx: AgentContext) -> dict:
    """Musteri: kendi siparisi mi diye sahiplik kontrolu yapar."""
    order = await orders_crud.get_by_id(ctx.db, order_id)
    if order is None:
        return {"error": "Boyle bir siparis bulamadim."}
    if ctx.customer_id is not None and order.customer_id != ctx.customer_id:
        return {"error": "Bu siparis size ait gorunmuyor. Tekrar kontrol eder misiniz?"}
    return _format_order(order)


async def list_my_recent_orders(*, days: int = 30, ctx: AgentContext) -> dict:
    if ctx.customer_id is None:
        return {"error": "Musteri kimligi belirsiz."}
    since = datetime.utcnow() - timedelta(days=days)
    orders = await orders_crud.list_orders(
        ctx.db, customer_id=ctx.customer_id, since=since, limit=20
    )
    return {"count": len(orders), "orders": [_format_order(o) for o in orders]}


async def list_orders(
    *,
    status: str | None = None,
    since_days: int | None = None,
    customer_id: int | None = None,
    limit: int = 20,
    ctx: AgentContext,
) -> dict:
    """Panel: tum siparisleri listeleme."""
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    status_enum = OrderStatus(status) if status else None
    since = datetime.utcnow() - timedelta(days=since_days) if since_days else None
    orders = await orders_crud.list_orders(
        ctx.db, status=status_enum, since=since, customer_id=customer_id, limit=limit
    )
    return {"count": len(orders), "orders": [_format_order(o) for o in orders]}


async def get_order_detail(order_id: int, *, ctx: AgentContext) -> dict:
    """Panel: detayli siparis goruntuleme."""
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    order = await orders_crud.get_by_id(ctx.db, order_id)
    if order is None:
        return {"error": "Siparis bulunamadi."}
    return _format_order(order)


# ---------- Draft / Confirm order flow ----------


async def _get_or_create_session(ctx: AgentContext) -> TelegramSession:
    if ctx.telegram_user_id is None:
        raise ValueError("telegram_user_id required for draft flow")
    res = await ctx.db.execute(
        select(TelegramSession).where(
            TelegramSession.telegram_user_id == ctx.telegram_user_id
        )
    )
    session = res.scalar_one_or_none()
    if session is None:
        session = TelegramSession(telegram_user_id=ctx.telegram_user_id)
        ctx.db.add(session)
        await ctx.db.flush()
    return session


async def create_order_draft(items: list[dict], *, ctx: AgentContext) -> dict:
    """items: [{"product_name": "domates", "quantity": 5.0}, ...]"""
    if ctx.customer_id is None:
        return {"error": "Musteri kimligi belirsiz."}
    resolved: list[dict] = []
    total = 0.0
    for it in items:
        name = it.get("product_name")
        qty = float(it.get("quantity", 0))
        if not name or qty <= 0:
            return {"error": f"Gecersiz urun girdisi: {it}"}
        matches = await products_crud.search_by_name(ctx.db, name, limit=1)
        if not matches:
            return {"error": f"'{name}' urunu bulunamadi."}
        p = matches[0]
        if p.stock < qty:
            return {
                "error": f"{p.name} stogu yetersiz ({p.stock} {p.unit} mevcut, {qty} istendi)."
            }
        resolved.append(
            {"product_id": p.id, "name": p.name, "quantity": qty, "unit_price": p.price}
        )
        total += p.price * qty

    draft_id = uuid.uuid4().hex[:8]
    payload = {"draft_id": draft_id, "items": resolved, "total": round(total, 2)}
    session = await _get_or_create_session(ctx)
    session.pending_intent = json.dumps(payload)
    await ctx.db.flush()
    return {"draft_id": draft_id, "items": resolved, "total": round(total, 2)}


async def confirm_order(draft_id: str, *, ctx: AgentContext) -> dict:
    """Inline buton callback'i tarafindan cagrilir."""
    if ctx.customer_id is None or ctx.telegram_user_id is None:
        return {"error": "Musteri kimligi belirsiz."}
    res = await ctx.db.execute(
        select(TelegramSession).where(
            TelegramSession.telegram_user_id == ctx.telegram_user_id
        )
    )
    session = res.scalar_one_or_none()
    if session is None or not session.pending_intent:
        return {"error": "Aktif siparis taslagi yok."}
    payload = json.loads(session.pending_intent)
    if payload.get("draft_id") != draft_id:
        return {"error": "Taslak suresi dolmus olabilir."}

    items_to_create = []
    for it in payload["items"]:
        p = await products_crud.get_by_id(ctx.db, it["product_id"])
        if p is None or p.stock < it["quantity"]:
            return {"error": f"{it['name']} icin stok yetersiz."}
        items_to_create.append((p, it["quantity"]))

    order = await orders_crud.create_order(
        ctx.db, customer_id=ctx.customer_id, items=items_to_create
    )
    session.pending_intent = None
    await ctx.db.flush()
    return {"order_id": order.id, "total": order.total, "status": order.status.value}


async def cancel_draft(*, ctx: AgentContext) -> dict:
    if ctx.telegram_user_id is None:
        return {"error": "Oturum bulunamadi."}
    res = await ctx.db.execute(
        select(TelegramSession).where(
            TelegramSession.telegram_user_id == ctx.telegram_user_id
        )
    )
    session = res.scalar_one_or_none()
    if session:
        session.pending_intent = None
        await ctx.db.flush()
    return {"cancelled": True}


# ---------- Panel: sales summary ----------


async def sales_summary(
    *,
    since_days: int = 7,
    group_by: str = "day",  # "day" veya "product"
    ctx: AgentContext,
) -> dict:
    if not ctx.is_admin:
        return {"error": "Yetki yok."}
    since = datetime.utcnow() - timedelta(days=since_days)
    orders = await orders_crud.list_orders(ctx.db, since=since, limit=1000)
    orders = [o for o in orders if o.status != OrderStatus.CANCELLED]

    if group_by == "day":
        buckets: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)
        for o in orders:
            key = o.created_at.date().isoformat()
            buckets[key] += o.total
            counts[key] += 1
        rows = [
            {"day": k, "revenue": round(v, 2), "order_count": counts[k]}
            for k, v in sorted(buckets.items())
        ]
        return {
            "group_by": "day",
            "rows": rows,
            "total_revenue": round(sum(buckets.values()), 2),
        }

    if group_by == "product":
        revenue: dict[str, float] = defaultdict(float)
        qty: dict[str, float] = defaultdict(float)
        for o in orders:
            for item in o.items:
                pname = item.product.name if item.product else "?"
                revenue[pname] += item.quantity * item.unit_price
                qty[pname] += item.quantity
        rows = sorted(
            [
                {"product": k, "revenue": round(v, 2), "quantity": qty[k]}
                for k, v in revenue.items()
            ],
            key=lambda x: x["revenue"],
            reverse=True,
        )
        return {"group_by": "product", "rows": rows[:20]}

    return {"error": f"Bilinmeyen group_by: {group_by}"}


async def top_products(*, since_days: int = 30, limit: int = 10, ctx: AgentContext) -> dict:
    if not ctx.is_admin:
        return {"error": "Yetki yok."}
    summary = await sales_summary(since_days=since_days, group_by="product", ctx=ctx)
    if "error" in summary:
        return summary
    return {"top": summary["rows"][:limit]}
