from fastapi import APIRouter

from app.api.v1 import carriers, chat, customers, dashboard, mock_cargo, orders, products, webhooks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(webhooks.router, tags=["webhooks"])
api_router.include_router(orders.router)
api_router.include_router(products.router)
api_router.include_router(customers.router)
api_router.include_router(dashboard.router)
api_router.include_router(mock_cargo.router)
api_router.include_router(carriers.router)
api_router.include_router(chat.router)
