from fastapi import APIRouter

from app.api.routes import (
    auth,
    backup,
    branches,
    clock,
    dashboard,
    expenses,
    sales,
    settings,
    staff,
    stock_counts,
    stock_deliveries,
    stock_items,
    stock_needs,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(backup.router)
api_router.include_router(branches.router)
api_router.include_router(staff.router)
api_router.include_router(clock.router)
api_router.include_router(stock_items.router)
api_router.include_router(stock_deliveries.router)
api_router.include_router(stock_needs.router)
api_router.include_router(stock_counts.router)
api_router.include_router(sales.router)
api_router.include_router(dashboard.router)
api_router.include_router(expenses.router)
api_router.include_router(settings.router)
