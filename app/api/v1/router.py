from fastapi import APIRouter

from app.api.v1 import webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(webhooks.router, tags=["webhooks"])
# Diger router'lar Phase 4'te eklenecek
