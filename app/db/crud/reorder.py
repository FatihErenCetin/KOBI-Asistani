"""Min/max stok seviyesine gore otomatik siparis onerileri."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import product_analytics as analytics_crud
from app.db.crud import product_suppliers as ps_crud
from app.db.models import Product


async def suggestions(db: AsyncSession) -> list[dict]:
    """low_stock_threshold (= min_stock) altindaki urunleri tedarikci bilgisiyle doner.

    suggested_order_qty hesabi:
    - max_stock varsa: max_stock - current_stock
    - yoksa: min_stock * 2 (varsayilan)
    Tedarikci: is_preferred=True olan link, yoksa ilk link.
    """
    res = await db.execute(
        select(Product).where(Product.is_active.is_(True))
    )
    out = []
    for p in res.scalars():
        if p.stock > p.low_stock_threshold:
            continue
        links = await ps_crud.list_for_product(db, p.id)
        preferred = next((l for l in links if l.is_preferred), None)
        chosen = preferred or (links[0] if links else None)
        if p.max_stock:
            qty = max(p.max_stock - p.stock, 0)
        else:
            qty = max(p.low_stock_threshold * 2, p.low_stock_threshold)
        # Lead-time tabanli oneri tarihi
        anal = await analytics_crud.for_product(db, p)
        days_of_stock = anal.get("days_of_stock")
        lead_time = chosen.lead_time_days if chosen else None
        recommended_date = None
        urgency = "info"
        if days_of_stock is None:
            # Hiç satış yok — hemen sipariş ver (stok zaten min altı)
            recommended_date = date.today().isoformat()
            urgency = "warning"
        elif lead_time is None:
            recommended_date = date.today().isoformat()
            urgency = "warning"
        else:
            days_until = days_of_stock - lead_time
            if days_until <= 0:
                recommended_date = date.today().isoformat()
                urgency = "critical"
            elif days_until <= 3:
                recommended_date = (
                    date.today() + timedelta(days=int(days_until))
                ).isoformat()
                urgency = "warning"
            else:
                recommended_date = (
                    date.today() + timedelta(days=int(days_until))
                ).isoformat()
                urgency = "info"

        out.append(
            {
                "product_id": p.id,
                "product_name": p.name,
                "unit": p.unit,
                "current_stock": p.stock,
                "min_stock": p.low_stock_threshold,
                "max_stock": p.max_stock,
                "suggested_order_qty": qty,
                "supplier_id": chosen.supplier_id if chosen else None,
                "supplier_name": (
                    chosen.supplier.name if chosen and chosen.supplier else None
                ),
                "lead_time_days": chosen.lead_time_days if chosen else None,
                "last_unit_cost": chosen.last_unit_cost if chosen else None,
                "estimated_cost": (
                    round(
                        ((chosen.last_unit_cost if chosen else None) or p.cost or 0)
                        * qty,
                        2,
                    )
                    if ((chosen and chosen.last_unit_cost) or p.cost)
                    else None
                ),
                "days_of_stock": days_of_stock,
                "recommended_order_date": recommended_date,
                "urgency": urgency,
            }
        )
    # Stoğu en az olanlar önce
    return sorted(out, key=lambda r: r["current_stock"])
