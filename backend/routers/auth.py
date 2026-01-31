from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db
from backend.database.redis import get_redis, RedisTokenCache
from backend.core.rate_limiter import limiter
from fastapi import HTTPException, status
from backend.core.config import settings
from backend.core.dependencies import get_current_user
from backend.models.user import User
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/auth", tags=["Authentication"])

@router.get("/spotify/login")
@limiter.limit("10/minute")
async def spotify_login(
    request: Request,
    response: Response,
):
    """Initiate Spotify OAuth flow"""
    auth_url = spotify_auth_service.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback")
@limiter.limit("5/minute")
async def spotify_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    """Handle Spotify OAuth callback"""
    try:
        access_token, refresh_token = await auth_service.handle_spotify_callback(
            code, db
        )

        redirect = RedirectResponse(
            url=f"{settings.frontend_url}/dashboard"
        )

        cookie_config = {
            "httponly": True,
            "samesite": settings.cookie_samesite,
            "secure": settings.cookie_secure,
            "domain": settings.cookie_domain,
        }

        redirect.set_cookie(
            key="access_token",
            value=access_token,
            max_age=3600,
            **cookie_config
        )

        redirect.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=2592000,
            **cookie_config
        )

        return redirect

    except Exception as e:
        logger.error(f"Spotify callback error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=auth_failed"
        )

@router.post("/refresh")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh the access token using the refresh token from cookie or header.
    Returns new access token and optionally sets it in cookies.
    """
    # Extract refresh token (similar to get_current_user logic)
    refresh_token = None

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        refresh_token = auth_header.split(" ")[1]

    if not refresh_token:
        refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        new_tokens = await auth_service.refresh_access_token(refresh_token)

        if request.cookies.get("refresh_token"):
            cookie_config = {
                "httponly": True,
                "samesite": settings.cookie_samesite,
                "secure": settings.cookie_secure,
                "domain": settings.cookie_domain,
            }

            response.set_cookie(
                key="access_token",
                value=new_tokens["access_token"],
                max_age=3600,
                **cookie_config
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
        # Only attempt cache invalidation if Redis is available
        if redis_client:
            cache = RedisTokenCache(redis_client)
            await cache.invalidate_token(current_user.spotify_id)
            logger.info(f"User {current_user.spotify_id} logged out (Cache cleared)")
        else:
            logger.info(f"User {current_user.spotify_id} logged out (Cache bypass - Redis down)")

    except Exception as e:
        logger.error(f"Logout cache error (non-fatal): {str(e)}")
        # We continue so cookies are still deleted

    cookie_config = {
        "httponly": True,
        "samesite": settings.cookie_samesite,
        "secure": settings.cookie_secure,
        "domain": settings.cookie_domain,
    }
    response.delete_cookie("access_token", **cookie_config)
    response.delete_cookie("refresh_token", **cookie_config)

    return {"message": "Logged out successfully"}

@router.get("/verify")
@limiter.limit("30/minute")
async def verify_token(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Verify if the current access token is valid.
    Useful for frontend to check authentication status.
    """
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "spotify_id": current_user.spotify_id,
        "email": current_user.email,
        "display_name": current_user.display_name,
    }
