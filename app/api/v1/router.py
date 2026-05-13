from fastapi import APIRouter

from app.api.v1 import (
    auth,
    chat,
    customers,
    dashboard,
    mock_cargo,
    orders,
    products,
    suppliers,
    warehouses,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(webhooks.router, tags=["webhooks"])
api_router.include_router(auth.router)
api_router.include_router(orders.router)
api_router.include_router(products.router)
api_router.include_router(suppliers.router)
api_router.include_router(warehouses.router)
api_router.include_router(customers.router)
api_router.include_router(dashboard.router)
api_router.include_router(mock_cargo.router)
api_router.include_router(chat.router)
