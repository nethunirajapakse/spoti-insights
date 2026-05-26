from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, UTC
import logging

from backend.exceptions.custom_exceptions import (
    SpotifyAuthError,
    UserNotFoundError,
    RefreshTokenMissingError
)
from backend.schemas.error import ErrorResponse

logger = logging.getLogger(__name__)


def spotify_auth_error_handler(request: Request, exc: SpotifyAuthError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            error="Authentication Error",
            detail=str(exc),
            status_code=401,
            path=str(request.url),
            timestamp=datetime.now(UTC).isoformat()
        ).dict()
    )


def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="User Not Found",
            detail=str(exc),
            status_code=404,
            path=str(request.url),
            timestamp=datetime.now(UTC).isoformat()
        ).dict()
    )


def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": "Invalid request data",
            "status_code": 422,
            "errors": exc.errors(),
            "timestamp": datetime.now(UTC).isoformat()
        }
    )


def database_error_handler(request: Request, exc: SQLAlchemyError):
    logger.exception("Database error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Database Error",
            detail="An error occurred while accessing the database",
            status_code=500,
            path=str(request.url),
            timestamp=datetime.now(UTC).isoformat()
        ).dict()
    )


def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            status_code=500,
            path=str(request.url),
            timestamp=datetime.now(UTC).isoformat()
        ).dict()
    )
