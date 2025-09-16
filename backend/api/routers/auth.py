from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.services import spotify_auth_service
from backend.database.connection import get_db
from backend.services import auth_service
from backend.api.schemas.user import UserResponse, SpotifyToken, RefreshTokenRequest
import httpx
from backend.exceptions.custom_exceptions import ( 
    AuthorizationCodeMissingError,
    SpotifyTokensError,
    SpotifyUserIDMissingError,
    UserNotFoundError,
    RefreshTokenMissingError
)

router = APIRouter(prefix="/public/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth_service.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=UserResponse) # UserResponse now contains the JWT
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    try:
        user_response = await auth_service.handle_spotify_callback(code, db)
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
