from datetime import datetime, timedelta

from sqlalchemy import select

from app.db.crud import orders as orders_crud
from app.db.models import Customer
from app.tools.base import AgentContext
from app.tools.order_tools import _format_order_compact


async def customer_order_history(
    name_or_id: str, *, since_days: int | None = None, ctx: AgentContext
) -> dict:
    if not ctx.is_admin:
        return {"error": "Bu islem icin yetkiniz yok."}
    customer: Customer | None = None
    try:
        cid = int(name_or_id)
        customer = await ctx.db.get(Customer, cid)
    except ValueError:
        pass
    if customer is None:
        pattern = f"%{name_or_id}%"
        res = await ctx.db.execute(
            select(Customer).where(Customer.name.ilike(pattern)).limit(1)
        )
        customer = res.scalar_one_or_none()
    if customer is None:
        return {"error": f"'{name_or_id}' adinda musteri bulamadim."}
    since = datetime.utcnow() - timedelta(days=since_days) if since_days else None
    orders = await orders_crud.list_orders(
        ctx.db, customer_id=customer.id, since=since, limit=10
    )
    total_spend = sum(o.total for o in orders)
    return {
        "customer": {"id": customer.id, "name": customer.name, "phone": customer.phone},
        "order_count": len(orders),
        "total_spend": round(total_spend, 2),
        "orders": [_format_order_compact(o) for o in orders],
    }
