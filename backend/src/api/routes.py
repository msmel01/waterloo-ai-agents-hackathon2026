from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.bookings import router as bookings_router
from src.api.v1.endpoints.chat import router as chat_router
from src.api.v1.endpoints.hearts import router as hearts_router
from src.api.v1.endpoints.public import router as public_router
from src.api.v1.endpoints.sessions import router as sessions_router
from src.api.v1.endpoints.suitors import router as suitors_router
from src.api.v1.endpoints.users import router as users_router

routers = APIRouter(prefix="/v1")

router_list = [
    users_router,
    auth_router,
    chat_router,
    hearts_router,
    public_router,
    suitors_router,
    sessions_router,
    bookings_router,
]

for router in router_list:
    routers.include_router(router)
