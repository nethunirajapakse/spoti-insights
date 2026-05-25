import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from backend.auth import spotify_auth
from backend.database.connection import get_db
from backend.services import auth_service
from backend.schemas.user import UserResponse, SpotifyToken, RefreshTokenRequest
import httpx
from backend.exceptions import ( 
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)

logger = logging.getLogger(__name__)

# 30-day lifetime for the spotify_id session cookie
_SPOTIFY_ID_COOKIE_MAX_AGE = 30 * 24 * 60 * 60

# Honor the COOKIE_SECURE env var; defaults to True so production is safe by default
_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() not in ("0", "false", "no")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login(request: Request, db: Session = Depends(get_db)):
    spotify_id = request.cookies.get("spotify_id")

    if spotify_id:
        try:
            new_tokens = await auth_service.refresh_user_spotify_access_token(db, spotify_id)
            return new_tokens
        except (UserNotFoundError, RefreshTokenMissingError, httpx.HTTPStatusError) as exc:
            logger.warning(
                "Silent token refresh failed for spotify_id=%s (%s). "
                "Falling back to full OAuth flow.",
                spotify_id,
                exc,
            )

    auth_url = spotify_auth.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=UserResponse)
async def spotify_callback(code: str, response: Response, db: Session = Depends(get_db)):
    try:
        user_response = await auth_service.handle_spotify_callback(code, db)
        response.set_cookie(
            key="spotify_id",
            value=user_response.spotify_id,
            httponly=True,
            samesite="lax",
            secure=_COOKIE_SECURE,
            max_age=_SPOTIFY_ID_COOKIE_MAX_AGE,
        )
        return user_response
    except (AuthorizationCodeMissingError, SpotifyTokensError, SpotifyUserIDMissingError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Spotify API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/spotify/refresh_access_token", response_model=SpotifyToken)
async def refresh_access_token_endpoint(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    try:
        new_tokens = await auth_service.refresh_user_spotify_access_token(db, request.spotify_id)
        return new_tokens
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RefreshTokenMissingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Spotify API refresh token error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during token refresh: {str(e)}"
        )