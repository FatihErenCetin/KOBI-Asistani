from sqlalchemy import select

from app.db.crud import orders as orders_crud
from app.db.models import Shipment
from app.integrations import cargo_mock
from app.tools.base import AgentContext


async def get_shipment_status(tracking_no: str, *, ctx: AgentContext) -> dict:
    res = await ctx.db.execute(select(Shipment).where(Shipment.tracking_no == tracking_no))
    s = res.scalar_one_or_none()
    if s is None:
        return {"error": "Bu takip numarasi bulunamadi."}
    if not ctx.is_admin and ctx.customer_id is not None:
        order = await orders_crud.get_by_id(ctx.db, s.order_id)
        if not order or order.customer_id != ctx.customer_id:
            return {"error": "Bu kargo size ait gorunmuyor."}
    return cargo_mock.get_status_summary(s)
