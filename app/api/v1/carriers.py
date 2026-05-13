from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.tools import carrier_tools
from app.tools.base import AgentContext

router = APIRouter(
    prefix="/carriers", tags=["carriers"], dependencies=[Depends(require_admin)]
)


@router.get("/performance")
async def carrier_performance(
    since_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    ctx = AgentContext(db=db, is_admin=True)
    return await carrier_tools.carrier_performance_analysis(
        since_days=since_days, ctx=ctx
    )


@router.get("/risks")
async def carrier_risks(db: AsyncSession = Depends(get_db)):
    ctx = AgentContext(db=db, is_admin=True)
    return await carrier_tools.high_complaint_risk_orders(ctx=ctx)
