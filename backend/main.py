from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from backend.routers import auth, user, analytics, health, deep_analytics
from backend.middleware.cors import configure_middleware
from backend.middleware.logging_middleware import RequestLoggingMiddleware
from backend.middleware.error_handler import (
    spotify_auth_error_handler,
    user_not_found_handler,
    validation_error_handler,
    database_error_handler,
    generic_error_handler,
)
from backend.exceptions.custom_exceptions import SpotifyAuthError, UserNotFoundError
from backend.core.config import settings, OPENAPI_TAGS, SWAGGER_UI_PARAMETERS
from backend.core.rate_limiter import limiter, rate_limit_handler
from backend.services import spotify_api_service
from backend.utils.openapi import customize_openapi
from backend.jobs.spotify_sync import start_scheduler


class RedisOutageFilter(logging.Filter):
    """
    Filters out noisy Redis connection errors from SlowAPI and limits libraries
    to keep the console clean during known outages or local development.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        noisy_messages = [
            "Failed to rate limit",
            "Error 10061 connecting",
            "target machine actively refused it",
            "ConnectionRefusedError",
        ]
        msg = record.getMessage()
        return not any(noisy_msg in msg for noisy_msg in noisy_messages)


logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)
logging.getLogger("slowapi").addFilter(RedisOutageFilter())
logging.getLogger("limits").addFilter(RedisOutageFilter())
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    try:
        spotify_api_service.init_spotify_client()
        logger.info("Spotify HTTP client initialized.")
        logger.info("Running in %s mode", settings.environment)

        try:
            scheduler = start_scheduler()
        except Exception:
            logger.exception("Failed to start sync scheduler; continuing without it.")

        yield
    finally:
        if scheduler is not None:
            try:
                scheduler.shutdown()
            except Exception:
                logger.exception("Error shutting down scheduler")
        try:
            await spotify_api_service.close_spotify_client()
            logger.info("Spotify HTTP client closed.")
        except Exception:
            logger.exception("Error closing Spotify HTTP client")


def create_app() -> FastAPI:
    """Application factory pattern for creating FastAPI instance."""
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        openapi_tags=OPENAPI_TAGS,
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        exception_handlers={
            RateLimitExceeded: rate_limit_handler,
            SpotifyAuthError: spotify_auth_error_handler,
            UserNotFoundError: user_not_found_handler,
            RequestValidationError: validation_error_handler,
            SQLAlchemyError: database_error_handler,
            Exception: generic_error_handler,
        },
    )

    app.state.limiter = limiter

    configure_middleware(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(analytics.router)
    app.include_router(health.router)
    app.include_router(deep_analytics.router)

    app.openapi = lambda: customize_openapi(app)
    return app


app = create_app()
