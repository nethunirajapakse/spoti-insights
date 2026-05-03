import secrets
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db
from backend.database.redis import get_redis, RedisTokenCache, JWTDenylist
from backend.core.rate_limiter import limiter
from backend.core.config import settings
from backend.core.dependencies import get_current_user
from backend.core.jwt_utils import decode_access_token
from backend.models.user import User
from backend.exceptions.custom_exceptions import SpotifyTokensError, SpotifyUserIDMissingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/auth", tags=["Authentication"])


@router.get("/spotify/login")
@limiter.limit("10/minute")
async def spotify_login(request: Request):
    """
    Initiate Spotify OAuth flow.
    Generates a cryptographically random state value, stores it in a
    short-lived httpOnly cookie, and returns the Spotify auth URL.
    """
    state = secrets.token_urlsafe(16)
    auth_url = spotify_auth_service.get_authorize_url(state)

    response = JSONResponse({"auth_url": auth_url})
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=settings.oauth_state_max_age,
        httponly=True,
        samesite="lax",         # lax so the cookie is sent on the redirect back
        secure=settings.cookie_secure,
        domain=settings.cookie_domain,
        path="/",
    )
    return response


@router.get("/spotify/callback")
@limiter.limit("5/minute")
async def spotify_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    stored_state = request.cookies.get("oauth_state")
    if not stored_state:
        logger.warning("OAuth state cookie missing from callback request")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=state_missing")
    if not secrets.compare_digest(state, stored_state):
        logger.warning("OAuth state mismatch — possible CSRF attempt")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=state_mismatch")

    try:
        access_token, refresh_token = await auth_service.handle_spotify_callback(code, db)
    except (SpotifyTokensError, SpotifyUserIDMissingError) as e:
        # Spotify rejected the code or returned an incomplete profile — user-facing
        logger.warning(f"Spotify auth rejected: {str(e)}")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=spotify_auth_failed")
    except Exception as e:
        # DB down, encryption error, etc. — server fault
        logger.error(f"Internal error during Spotify callback: {str(e)}", exc_info=True)
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=server_error")

    redirect = RedirectResponse(url=f"{settings.frontend_url}/dashboard")

    cookie_config = {
        "httponly": True,
        "samesite": settings.cookie_samesite,
        "secure": settings.cookie_secure,
        "domain": settings.cookie_domain,
        "path": "/",
    }

    redirect.delete_cookie("oauth_state", path="/", domain=settings.cookie_domain)
    redirect.set_cookie(key="access_token", value=access_token, max_age=settings.access_token_max_age, **cookie_config)
    redirect.set_cookie(key="refresh_token", value=refresh_token, max_age=settings.refresh_token_max_age, **cookie_config)

    return redirect


@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    response: Response,
    redis_client=Depends(get_redis),
):
    """
    Validates the refresh token, issues a new access token, and rotates
    the refresh token. The consumed refresh token's jti is denylisted so
    it cannot be reused even while technically unexpired.
    """
    refresh_token_value = None
    from_cookie = False

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token_value = auth_header.split(" ")[1]

    if not refresh_token_value:
        refresh_token_value = request.cookies.get("refresh_token")
        if refresh_token_value:
            from_cookie = True

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        new_tokens = await auth_service.refresh_access_token(refresh_token_value)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    old_refresh_jti = new_tokens["old_refresh_jti"]

    # Denylist the consumed refresh token
    denylist = JWTDenylist(redis_client)
    if old_refresh_jti:
        # Remaining TTL of the old token — decode it to get exp
        try:
            old_payload = decode_refresh_token(refresh_token_value)
            exp = old_payload.get("exp", 0)
            remaining_ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
        except Exception:
            # If we can't decode it here something is very wrong; use a safe fallback
            remaining_ttl = settings.refresh_token_expire_days * 86400

        await denylist.add(old_refresh_jti, remaining_ttl)

    cookie_config = {
        "httponly": True,
        "samesite": settings.cookie_samesite,
        "secure": settings.cookie_secure,
        "domain": settings.cookie_domain,
        "path": "/",
    }

    if from_cookie:
        response.set_cookie(
            key="access_token",
            value=new_tokens["access_token"],
            max_age=settings.access_token_max_age,
            **cookie_config,
        )
        # Rotate the refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_tokens["refresh_token"],
            max_age=settings.refresh_token_max_age,
            **cookie_config,
        )

    logger.info("Access and refresh tokens rotated successfully")
    return {
        "message": "Token refreshed successfully",
        "access_token": new_tokens["access_token"],
        "refresh_token": new_tokens["refresh_token"],
        "token_type": "bearer",
    }


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    """
    Logs the user out by:
    1. Denylisting the current access token jti so it is rejected immediately.
    2. Denylisting the current refresh token jti so it cannot be rotated into
       a new access token.
    3. Clearing the Spotify token cache entry.
    4. Deleting the auth cookies.
    """
    denylist = JWTDenylist(redis_client)

    # Denylist the access token
    access_token_value = request.cookies.get("access_token")
    auth_header = request.headers.get("Authorization")
    if not access_token_value and auth_header and auth_header.startswith("Bearer "):
        access_token_value = auth_header.split(" ")[1]

    if access_token_value:
        try:
            payload = decode_access_token(access_token_value)
            jti = payload.get("jti")
            exp = payload.get("exp", 0)
            if jti:
                remaining_ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
                await denylist.add(jti, remaining_ttl)
                logger.info(f"Access token jti={jti} denylisted for user {current_user.spotify_id}")
        except Exception as e:
            logger.warning(f"Could not denylist access token on logout: {e}")

    # Denylist the refresh token
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        try:
            payload = decode_refresh_token(refresh_token_value)
            jti = payload.get("jti")
            exp = payload.get("exp", 0)
            if jti:
                remaining_ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
                await denylist.add(jti, remaining_ttl)
                logger.info(f"Refresh token jti={jti} denylisted for user {current_user.spotify_id}")
        except Exception as e:
            logger.warning(f"Could not denylist refresh token on logout: {e}")

    # Clear Spotify token cache
    try:
        if redis_client:
            cache = RedisTokenCache(redis_client)
            await cache.invalidate_token(current_user.spotify_id)
    except Exception as e:
        logger.error(f"Logout cache error (non-fatal): {str(e)}")

    response.delete_cookie("access_token", path="/", domain=settings.cookie_domain)
    response.delete_cookie("refresh_token", path="/", domain=settings.cookie_domain)

    return {"message": "Logged out successfully"}


@router.get("/verify")
@limiter.limit("30/minute")
async def verify_token(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Verify if the current access token is valid."""
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "spotify_id": current_user.spotify_id,
        "email": current_user.email,
        "display_name": current_user.display_name,
    }
