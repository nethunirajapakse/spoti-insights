from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.auth import spotify_auth
from backend.database.connection import get_db
from backend.services import auth_service 
from backend.schemas.user import UserResponse, SpotifyToken
import httpx

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/spotify/login")
async def spotify_login():
    auth_url = spotify_auth.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/spotify/callback", response_model=UserResponse)
async def spotify_callback(code: str, db: Session = Depends(get_db)):
    try:
        user_response = await auth_service.handle_spotify_callback(code, db)
        return user_response
    except ValueError as e:
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
async def refresh_access_token_endpoint(spotify_id: str, db: Session = Depends(get_db)):
    try:
        new_tokens = await auth_service.refresh_user_spotify_access_token(db, spotify_id)
        return new_tokens
    except ValueError as e:
        if "User not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
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