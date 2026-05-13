from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.jobs.cargo_advance import advance_active_shipments
from app.agents.proactive_agent import run_proactive_notifications
from app.jobs.morning_briefing import send_morning_briefing
from app.jobs.stock_forecast import run_stock_forecast

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

    if settings.PROACTIVE_NOTIFICATIONS_ENABLED:
        scheduler.add_job(
            run_proactive_notifications,
            "interval",
            minutes=settings.PROACTIVE_NOTIFICATIONS_INTERVAL_MIN,
            id="proactive_notifications",
        )

    if settings.MORNING_BRIEFING_ENABLED:
        scheduler.add_job(
            send_morning_briefing,
            "cron",
            hour=settings.MORNING_BRIEFING_HOUR,
            minute=settings.MORNING_BRIEFING_MINUTE,
            id="morning_briefing",
        )

    if settings.STOCK_FORECAST_ENABLED:
        scheduler.add_job(
            run_stock_forecast,
            "interval",
            hours=settings.STOCK_FORECAST_INTERVAL_HOURS,
            id="stock_forecast",
        )

    if scheduler.get_jobs():
        scheduler.start()

    yield

    if scheduler and scheduler.running:
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