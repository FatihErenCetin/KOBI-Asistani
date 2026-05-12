from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, require_admin
from app.db.crud import orders as orders_crud
from app.db.crud import products as products_crud
from app.db.models import Order, OrderStatus, Shipment
from app.schemas.dashboard import (
    DashboardToday,
    LowStockRow,
    PendingOrderRow,
    ShipmentTodayRow,
    SummaryStats,
)

router = APIRouter(
    prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_admin)]
)


@router.get("/today", response_model=DashboardToday)
async def dashboard_today(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_48h = now - timedelta(hours=48)
    today_d = date.today()

    n_24h = (
        await db.execute(
            select(func.count(Order.id)).where(Order.created_at >= last_24h)
        )
    ).scalar_one()
    rev_24h = await orders_crud.revenue_since(db, last_24h)
    rev_prev = await orders_crud.revenue_since(db, last_48h) - rev_24h
    pct = ((rev_24h - rev_prev) / rev_prev * 100) if rev_prev > 0 else 0.0

    pending_count = await orders_crud.count_by_status(db, OrderStatus.PENDING)
    prepared_count = await orders_crud.count_by_status(db, OrderStatus.PREPARED)

    urgent = (
        await db.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.status.in_([OrderStatus.PENDING, OrderStatus.PREPARED]),
                    Order.promised_delivery <= today_d,
                )
            )
        )
    ).scalar_one()

    shipments_today = (
        await db.execute(
            select(func.count(Shipment.id)).where(
                Shipment.estimated_delivery == today_d
            )
        )
    ).scalar_one()

    low_products = await products_crud.list_all(db, low_stock_only=True)

    pending_orders = await orders_crud.list_orders(
        db, status=OrderStatus.PENDING, limit=10
    )
    recent_orders = await orders_crud.list_orders(db, since=last_24h, limit=10)

    shipments_today_res = await db.execute(
        select(Shipment)
        .where(Shipment.estimated_delivery == today_d)
        .options(selectinload(Shipment.order).selectinload(Order.customer))
        .limit(20)
    )
    shipments_today_list = list(shipments_today_res.scalars())

    return DashboardToday(
        summary=SummaryStats(
            orders_last_24h=int(n_24h),
            revenue_last_24h=round(rev_24h, 2),
            orders_vs_yesterday_pct=round(pct, 1),
            pending_to_prepare=pending_count + prepared_count,
            urgent_today=int(urgent),
            shipments_today=int(shipments_today),
            low_stock_count=len(low_products),
        ),
        pending_orders=[
            PendingOrderRow(
                id=o.id,
                customer_name=o.customer.name,
                total=o.total,
                status=o.status.value,
                created_at=o.created_at,
                promised_delivery=o.promised_delivery,
            )
            for o in pending_orders
        ],
        todays_shipments=[
            ShipmentTodayRow(
                order_id=s.order_id,
                tracking_no=s.tracking_no,
                customer_name=s.order.customer.name
                if s.order and s.order.customer
                else "?",
                status=s.status.value,
                current_location=s.current_location,
                eta=s.estimated_delivery,
            )
            for s in shipments_today_list
        ],
        low_stock_items=[
            LowStockRow(
                id=p.id,
                name=p.name,
                stock=p.stock,
                low_stock_threshold=p.low_stock_threshold,
                unit=p.unit,
            )
            for p in low_products
        ],
        recent_orders=[
            PendingOrderRow(
                id=o.id,
                customer_name=o.customer.name,
                total=o.total,
                status=o.status.value,
                created_at=o.created_at,
                promised_delivery=o.promised_delivery,
            )
            for o in recent_orders
        ],
    )
