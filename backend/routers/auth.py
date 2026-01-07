from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db
from backend.core.rate_limiter import limiter
from fastapi import Request
from backend.core.config import settings
import logging 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/auth", tags=["Authentication"])

@router.get("/spotify/login")
@limiter.limit("10/minute")  # Max 10 login attempts per minute
async def spotify_login(request: Request):
    auth_url = spotify_auth_service.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback")
@limiter.limit("5/minute")  # Max 5 callback attempts per minute
async def spotify_callback(
    request: Request,
    code: str, 
    db: Session = Depends(get_db)
):
    try:
        access_token, refresh_token = await auth_service.handle_spotify_callback(code, db)
        
        response = RedirectResponse(url=f"{settings.frontend_url}/dashboard")
        
        # Secure cookie configuration
        cookie_config = {
            "httponly": True,
            "samesite": settings.cookie_samesite,
            "secure": settings.cookie_secure,
            "domain": settings.cookie_domain
        }
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=3600,
            **cookie_config
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=2592000,
            **cookie_config
        )
        
        return response
    except Exception as e:
        logger.error(f"Spotify callback error: {str(e)}")
        return RedirectResponse(url=f"{settings.frontend_url}/login?error=auth_failed")