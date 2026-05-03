from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.database.connection import get_db
from backend.database.redis import get_redis, JWTDenylist
from backend.core.jwt_utils import decode_access_token
from backend.services import user_service
from backend.models.user import User
from backend.exceptions.custom_exceptions import UserNotFoundError
import logging

logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    redis_client=Depends(get_redis),
) -> User:
    """
    Hybrid dependency: checks for JWT in the Authorization header first,
    then falls back to the 'access_token' cookie.

    After decoding, the token's jti is checked against the Redis denylist
    so that logged-out tokens are rejected even while still technically
    unexpired. Redis unavailability is fail-open (logged but not fatal).
    """
    token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error decoding access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    spotify_id: str | None = payload.get("sub")
    jti: str | None = payload.get("jti")

    if not spotify_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    denylist = JWTDenylist(redis_client)
    if jti:
        if await denylist.is_denied(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        logger.debug("Token missing jti claim — denylist check skipped (pre-rollout token)")

    # Cache payload for downstream handlers (e.g. /logout avoids a second decode)
    request.state.token_payload = payload

    try:
        return user_service.get_user_by_spotify_id(db, spotify_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
    except SQLAlchemyError:
        logger.exception("Database error in get_current_user for sub=%s", spotify_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable.",
        )
