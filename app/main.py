from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.jobs.cargo_advance import advance_active_shipments

scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    setup_logging()
    if settings.CARGO_AUTO_ADVANCE:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            advance_active_shipments,
            "interval",
            minutes=settings.CARGO_AUTO_ADVANCE_INTERVAL_MIN,
            id="cargo_advance",
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
