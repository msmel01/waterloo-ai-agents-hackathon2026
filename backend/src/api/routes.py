from fastapi import APIRouter

from src.api.v1.endpoints.admin import router as admin_router
from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.bookings import router as bookings_router
from src.api.v1.endpoints.dashboard import router as dashboard_router
from src.api.v1.endpoints.public import router as public_router
from src.api.v1.endpoints.sessions import router as sessions_router
from src.api.v1.endpoints.suitors import router as suitors_router

routers = APIRouter(prefix="/v1")

router_list = [
    auth_router,
    admin_router,
    public_router,
    suitors_router,
    sessions_router,
    bookings_router,
    dashboard_router,
]

for router in router_list:
    routers.include_router(router)
