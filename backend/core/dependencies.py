from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
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

    # 1. Try Authorization header (API clients / Postman)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # 2. Fall back to cookie (browser)
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Decode — raises 401 on invalid signature, expiry, or wrong type
    try:
        payload = decode_access_token(token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    spotify_id: str = payload.get("sub")
    jti: str = payload.get("jti")

    if not spotify_id or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    # 4. Denylist check — fail-open if Redis is down (JWTDenylist handles logging)
    denylist = JWTDenylist(redis_client)
    if await denylist.is_denied(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Load user from DB
    try:
        return user_service.get_user_by_spotify_id(db, spotify_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )
