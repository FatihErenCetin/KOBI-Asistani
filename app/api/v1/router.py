from fastapi import APIRouter

from app.api.v1 import (
    admin_tools,
    auth,
    chat,
    complaints,
    customers,
    dashboard,
    finance,
    lot_actions,
    mock_cargo,
    orders,
    products,
    reorder,
    social,
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
api_router.include_router(reorder.router)
api_router.include_router(complaints.router)
api_router.include_router(admin_tools.router)
api_router.include_router(lot_actions.router)
api_router.include_router(finance.router)
api_router.include_router(customers.router)
api_router.include_router(dashboard.router)
api_router.include_router(mock_cargo.router)
api_router.include_router(chat.router)
api_router.include_router(social.router)
