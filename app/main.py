from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import SessionLocal
from app.jobs.cargo_advance import advance_active_shipments
from app.services.morning_briefing import send_briefings
from app.services.proactive_risk_scanner import scan_and_report

scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    setup_logging()
    scheduler = AsyncIOScheduler()
    if settings.CARGO_AUTO_ADVANCE:
        scheduler.add_job(
            advance_active_shipments,
            "interval",
            minutes=settings.CARGO_AUTO_ADVANCE_INTERVAL_MIN,
            id="cargo_advance",
        )
    # Sabah brifingi — her gun 09:00 (server timezone)
    scheduler.add_job(
        send_briefings,
        CronTrigger(hour=9, minute=0),
        id="morning_briefing",
        replace_existing=True,
    )

    # Proaktif risk taraması — saatte bir
    async def _scan_job():
        async with SessionLocal() as session:
            await scan_and_report(session)

    scheduler.add_job(
        _scan_job,
        CronTrigger(minute=15),  # her saatin 15. dakikası
        id="proactive_risk_scan",
        replace_existing=True,
    )
    scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown()


app = FastAPI(
    title="Akilli KOBI/Kooperatif Asistani",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.APP_ENV}
