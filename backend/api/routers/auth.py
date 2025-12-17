from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.services import auth_service, spotify_auth_service
from backend.database.connection import get_db
from backend.api.schemas.user import TokenResponse
import httpx
from backend.exceptions.custom_exceptions import ( 
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError
)

router = APIRouter(prefix="/public/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth_service.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=TokenResponse)
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    try:
        access_token, refresh_token = await auth_service.handle_spotify_callback(code, db)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
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
