from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from backend.routers import auth, user, analytics, health
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

# Configure logging based on environment
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    spotify_api_service.init_spotify_client()
    logger.info("Spotify HTTP client initialized.")
    logger.info("Running in %s mode", settings.environment)

    yield

    await spotify_api_service.close_spotify_client()
    logger.info("Spotify HTTP client closed.")


def create_app() -> FastAPI:
    """Application factory pattern for creating FastAPI instance."""
    
    # Initialize FastAPI app with OpenAPI documentation and exception handlers
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

    # Rate limiting
    app.state.limiter = limiter

    # Middleware (executed in reverse order)
    configure_middleware(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # Routers
    app.include_router(auth.router)
    app.include_router(user.router)
    app.include_router(analytics.router)
    app.include_router(health.router)
    # Custom OpenAPI schema
    app.openapi = lambda: customize_openapi(app)

    return app


# Create application instance
app = create_app()
