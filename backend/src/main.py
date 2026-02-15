import logging
import os

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.api.mcps import router as mcps_routers
from src.api.routes import routers
from src.core.config import config
from src.core.container import Container
from src.core.events import lifespan
from src.core.exception_handlers import (
    auth_error_handler,
    duplicated_error_handler,
    global_exception_handler,
    not_found_error_handler,
    not_satisfiable_error_handler,
    permission_denied_error_handler,
    request_validation_exception_handler,
    sqlalchemy_exception_handler,
    unauthorized_error_handler,
    validation_error_handler,
)
from src.core.exceptions import (
    AuthError,
    DuplicatedError,
    NotFoundError,
    NotSatisfiableError,
    PermissionDeniedError,
    UnauthorizedError,
    ValidationError,
)
from src.core.observability import configure_sentry, configure_structlog
from src.core.rate_limit import InMemoryRateLimiter, limiter
from src.util.class_object import singleton

logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
except Exception:  # pragma: no cover - optional dependency
    Limiter = None  # type: ignore[assignment]
    _rate_limit_exceeded_handler = None  # type: ignore[assignment]
    RateLimitExceeded = Exception  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]


@singleton
class AppCreator:
    def __init__(self):
        configure_structlog()
        configure_sentry()
        self.app = FastAPI(
            title="Valentine Hotline API",
            description="AI-powered dating screening system API",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc",
            version="0.1.0",
            root_path=os.getenv("API_ROOT_PATH", "/"),
            lifespan=lifespan,
        )

        self._configure_monitoring()

        self.container = Container()
        self.container.wire(modules=self.container.wiring_config.modules)
        self.app.state.container = self.container
        self.db = self.container.database()
        self.app.state.rate_limiter = InMemoryRateLimiter()
        if Limiter is not None and get_remote_address is not None:
            self.app.state.limiter = limiter
            if _rate_limit_exceeded_handler is not None:
                self.app.add_exception_handler(
                    RateLimitExceeded, _rate_limit_exceeded_handler
                )

        if config.BACKEND_CORS_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in config.BACKEND_CORS_ORIGINS],
                allow_credentials=False,
                allow_methods=["GET", "POST", "PATCH", "OPTIONS", "DELETE", "PUT"],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Dashboard-Key",
                    "X-Admin-Key",
                ],
            )
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.BACKEND_ALLOWED_HOSTS or ["localhost", "127.0.0.1"],
        )
        self.app.add_middleware(CorrelationIdMiddleware)
        self._register_middlewares()

        self.app.include_router(routers, prefix=config.API_STR)
        self.app.include_router(mcps_routers, prefix=config.API_STR)
        self._register_health_endpoint()
        mcp = FastApiMCP(self.app)
        mcp.mount_http(mount_path=config.MCP_STR)
        self._register_exception_handlers()

    def _configure_monitoring(self):
        try:
            FastAPIInstrumentor().instrument_app(self.app)

            logger.info("Instrumentation configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure instrumentation: {str(e)}")

    def _register_exception_handlers(self):
        self.app.add_exception_handler(
            RequestValidationError, request_validation_exception_handler
        )
        self.app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

        custom_exceptions = [
            (DuplicatedError, duplicated_error_handler),
            (AuthError, auth_error_handler),
            (NotFoundError, not_found_error_handler),
            (ValidationError, validation_error_handler),
            (PermissionDeniedError, permission_denied_error_handler),
            (UnauthorizedError, unauthorized_error_handler),
            (NotSatisfiableError, not_satisfiable_error_handler),
        ]
        for exception_class, handler in custom_exceptions:
            self.app.add_exception_handler(exception_class, handler)

        self.app.add_exception_handler(Exception, global_exception_handler)

    def _register_middlewares(self):
        @self.app.middleware("http")
        async def add_api_version_header(request, call_next):
            # Body size guard to avoid oversized payload abuse.
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > config.MAX_REQUEST_BODY_BYTES:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "Request body too large"},
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid Content-Length header"},
                    )

            retry_after = await self.app.state.rate_limiter.check_request(request)
            if retry_after is not None:
                logger.warning(
                    "Rate limit hit for %s %s", request.method, request.url.path
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please try again later.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            response = await call_next(request)
            response.headers["X-API-Version"] = "1.0"
            return response

    def _register_health_endpoint(self):
        @self.app.get("/health", tags=["System"])
        async def health():
            db_status = "ok"
            try:
                async with self.db.session() as session:
                    await session.execute(text("SELECT 1"))
            except Exception:
                db_status = "error"
            return {
                "status": "ok" if db_status == "ok" else "degraded",
                "db": db_status,
            }


app_creator = AppCreator()
app = app_creator.app
db = app_creator.db
container = app_creator.container
