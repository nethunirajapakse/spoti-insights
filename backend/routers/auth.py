import secrets
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db
from backend.database.redis import get_redis, RedisTokenCache
from backend.core.rate_limiter import limiter
from backend.core.config import settings
from backend.core.dependencies import get_current_user
from backend.models.user import User

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
    # 1. CSRF Check: Compare incoming state to the one in our cookie
    stored_state = request.cookies.get("oauth_state")
    if not secrets.compare_digest(state, stored_state or ""):
        logger.warning("OAuth state mismatch")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=state_mismatch")

    try:
        # 2. Exchange code for tokens
        access_token, refresh_token = await auth_service.handle_spotify_callback(code, db)

        # 3. Setup Response & Cookies
        redirect = RedirectResponse(url=f"{settings.frontend_url}/dashboard")
        
        cookie_config = {
            "httponly": True,
            "samesite": settings.cookie_samesite,
            "secure": settings.cookie_secure,
            "domain": settings.cookie_domain,
            "path": "/",
        }

        # We delete it here on success just to be tidy, but even this is optional
        redirect.delete_cookie("oauth_state", path="/", domain=settings.cookie_domain)

        redirect.set_cookie(key="access_token", value=access_token, max_age=settings.access_token_max_age, **cookie_config)
        redirect.set_cookie(key="refresh_token", value=refresh_token, max_age=settings.refresh_token_max_age, **cookie_config)

        return redirect

    except Exception as e:
        logger.error(f"Spotify callback error: {str(e)}")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=auth_failed")
@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Refresh the access token using the refresh token from cookie or header.
    Returns a new access token and optionally sets it in cookies.
    """
    refresh_token_value = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token_value = auth_header.split(" ")[1]

    if not refresh_token_value:
        refresh_token_value = request.cookies.get("refresh_token")

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        new_tokens = await auth_service.refresh_access_token(refresh_token_value)

        if request.cookies.get("refresh_token"):
            response.set_cookie(
                key="access_token",
                value=new_tokens["access_token"],
                max_age=settings.access_token_max_age,
                httponly=True,
                samesite=settings.cookie_samesite,
                secure=settings.cookie_secure,
                domain=settings.cookie_domain,
                path="/",
            )

        logger.info("Access token refreshed successfully")
        return {
            "message": "Token refreshed successfully",
            "access_token": new_tokens["access_token"],
            "token_type": "bearer",
        }

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    redis_client=Depends(get_redis),
):
    try:
        if redis_client:
            cache = RedisTokenCache(redis_client)
            await cache.invalidate_token(current_user.spotify_id)
            logger.info(f"User {current_user.spotify_id} logged out (cache cleared)")
        else:
            logger.info(f"User {current_user.spotify_id} logged out (cache bypass — Redis down)")
    except Exception as e:
        logger.error(f"Logout cache error (non-fatal): {str(e)}")

    response.delete_cookie("access_token",  path="/", domain=settings.cookie_domain)
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
